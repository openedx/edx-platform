# Copyright (c) 2014, 2021, Oracle and/or its affiliates.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License, version 2.0, as
# published by the Free Software Foundation.
#
# This program is also distributed with certain software (including
# but not limited to OpenSSL) that is licensed under separate terms,
# as designated in a particular file or component or in included license
# documentation.  The authors of MySQL hereby grant you an
# additional permission to link the program and your derivative works
# with the separately licensed software that they have included with
# MySQL.
#
# Without limiting anything contained in the foregoing, this file,
# which is part of MySQL Connector/Python, is also subject to the
# Universal FOSS Exception, version 1.0, a copy of which can be found at
# http://oss.oracle.com/licenses/universal-foss-exception.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License, version 2.0, for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA

"""Cursor classes using the C Extension
"""

from collections import namedtuple
import re
import weakref

from _mysql_connector import MySQLInterfaceError  # pylint: disable=F0401,E0611

from .abstracts import (MySQLConnectionAbstract, MySQLCursorAbstract,
                        NAMED_TUPLE_CACHE)
from . import errors
from .errorcode import CR_NO_RESULT_SET

from .cursor import (
    RE_PY_PARAM, RE_SQL_INSERT_STMT,
    RE_SQL_ON_DUPLICATE, RE_SQL_COMMENT, RE_SQL_INSERT_VALUES,
    RE_SQL_SPLIT_STMTS, RE_SQL_FIND_PARAM
)

ERR_NO_RESULT_TO_FETCH = "No result set to fetch from"


class _ParamSubstitutor(object):

    """
    Substitutes parameters into SQL statement.
    """

    def __init__(self, params):
        self.params = params
        self.index = 0

    def __call__(self, matchobj):
        index = self.index
        self.index += 1
        try:
            return self.params[index]
        except IndexError:
            raise errors.ProgrammingError(
                "Not enough parameters for the SQL statement")

    @property
    def remaining(self):
        """Returns number of parameters remaining to be substituted"""
        return len(self.params) - self.index


class CMySQLCursor(MySQLCursorAbstract):

    """Default cursor for interacting with MySQL using C Extension"""

    _raw = False
    _buffered = False
    _raw_as_string = False

    def __init__(self, connection):
        """Initialize"""
        MySQLCursorAbstract.__init__(self)

        self._insert_id = 0
        self._warning_count = 0
        self._warnings = None
        self._affected_rows = -1
        self._rowcount = -1
        self._nextrow = (None, None)
        self._executed = None
        self._executed_list = []
        self._stored_results = []

        if not isinstance(connection, MySQLConnectionAbstract):
            raise errors.InterfaceError(errno=2048)
        self._cnx = weakref.proxy(connection)

    def reset(self, free=True):
        """Reset the cursor

        When free is True (default) the result will be freed.
        """
        self._rowcount = -1
        self._nextrow = None
        self._affected_rows = -1
        self._insert_id = 0
        self._warning_count = 0
        self._warnings = None
        self._warnings = None
        self._warning_count = 0
        self._description = None
        self._executed_list = []
        if free and self._cnx:
            self._cnx.free_result()
        super(CMySQLCursor, self).reset()


    def _check_executed(self):
        """Check if the statement has been executed.

        Raises an error if the statement has not been executed.
        """
        if self._executed is None:
            raise errors.InterfaceError(ERR_NO_RESULT_TO_FETCH)

    def _fetch_warnings(self):
        """Fetch warnings

        Fetch warnings doing a SHOW WARNINGS. Can be called after getting
        the result.

        Returns a result set or None when there were no warnings.

        Raises errors.Error (or subclass) on errors.

        Returns list of tuples or None.
        """
        warnings = []
        try:
            # force freeing result
            self._cnx.consume_results()
            _ = self._cnx.cmd_query("SHOW WARNINGS")
            warnings = self._cnx.get_rows()[0]
            self._cnx.consume_results()
        except MySQLInterfaceError as exc:
            raise errors.get_mysql_exception(msg=exc.msg, errno=exc.errno,
                                             sqlstate=exc.sqlstate)
        except Exception as err:
            raise errors.InterfaceError(
                "Failed getting warnings; {0}".format(str(err)))

        if warnings:
            return warnings

        return None

    def _handle_warnings(self):
        """Handle possible warnings after all results are consumed"""
        if self._cnx.get_warnings is True and self._warning_count:
            self._warnings = self._fetch_warnings()

    def _handle_result(self, result):
        """Handles the result after statement execution"""
        if 'columns' in result:
            self._description = result['columns']
            self._rowcount = 0
            self._handle_resultset()
        else:
            self._insert_id = result['insert_id']
            self._warning_count = result['warning_count']
            self._affected_rows = result['affected_rows']
            self._rowcount = -1
            self._handle_warnings()
            if self._cnx.raise_on_warnings is True and self._warnings:
                raise errors.get_mysql_exception(*self._warnings[0][1:3])

    def _handle_resultset(self):
        """Handle a result set"""
        pass

    def _handle_eof(self):
        """Handle end of reading the result

        Raises an errors.Error on errors.
        """
        self._warning_count = self._cnx.warning_count
        self._handle_warnings()
        if self._cnx.raise_on_warnings is True and self._warnings:
            raise errors.get_mysql_exception(*self._warnings[0][1:3])

        if not self._cnx.more_results:
            self._cnx.free_result()

    def _execute_iter(self):
        """Generator returns MySQLCursor objects for multiple statements

        Deprecated: use nextset() method directly.

        This method is only used when multiple statements are executed
        by the execute() method. It uses zip() to make an iterator from the
        given query_iter (result of MySQLConnection.cmd_query_iter()) and
        the list of statements that were executed.
        """
        executed_list = RE_SQL_SPLIT_STMTS.split(self._executed)
        i = 0
        self._executed = executed_list[i]
        yield self

        while True:
            try:
                if not self.nextset():
                    raise StopIteration
            except errors.InterfaceError as exc:
                # Result without result set
                if exc.errno != CR_NO_RESULT_SET:
                    raise
            except StopIteration:
                return
            i += 1
            try:
                self._executed = executed_list[i].strip()
            except IndexError:
                self._executed = executed_list[0]
            yield self
        return

    def execute(self, operation, params=(), multi=False):
        """Execute given statement using given parameters

        Deprecated: The multi argument is not needed and nextset() should
        be used to handle multiple result sets.
        """
        if not operation:
            return None

        if not self._cnx or self._cnx.is_closed():
            raise errors.ProgrammingError("Cursor is not connected", 2055)
        self._cnx.handle_unread_result()

        stmt = ''
        self.reset()

        try:
            if isinstance(operation, str):
                stmt = operation.encode(self._cnx.python_charset)
            else:
                stmt = operation
        except (UnicodeDecodeError, UnicodeEncodeError) as err:
            raise errors.ProgrammingError(str(err))

        if params:
            prepared = self._cnx.prepare_for_mysql(params)
            if isinstance(prepared, dict):
                for key, value in prepared.items():
                    stmt = stmt.replace("%({0})s".format(key).encode(), value)
            elif isinstance(prepared, (list, tuple)):
                psub = _ParamSubstitutor(prepared)
                stmt = RE_PY_PARAM.sub(psub, stmt)
                if psub.remaining != 0:
                    raise errors.ProgrammingError(
                        "Not all parameters were used in the SQL statement")

        try:
            result = self._cnx.cmd_query(stmt, raw=self._raw,
                                         buffered=self._buffered,
                                         raw_as_string=self._raw_as_string)
        except MySQLInterfaceError as exc:
            raise errors.get_mysql_exception(msg=exc.msg, errno=exc.errno,
                                             sqlstate=exc.sqlstate)

        self._executed = stmt
        self._handle_result(result)

        if multi:
            return self._execute_iter()

        return None

    def _batch_insert(self, operation, seq_params):
        """Implements multi row insert"""
        def remove_comments(match):
            """Remove comments from INSERT statements.

            This function is used while removing comments from INSERT
            statements. If the matched string is a comment not enclosed
            by quotes, it returns an empty string, else the string itself.
            """
            if match.group(1):
                return ""
            return match.group(2)

        tmp = re.sub(RE_SQL_ON_DUPLICATE, '',
                     re.sub(RE_SQL_COMMENT, remove_comments, operation))

        matches = re.search(RE_SQL_INSERT_VALUES, tmp)
        if not matches:
            raise errors.InterfaceError(
                "Failed rewriting statement for multi-row INSERT. "
                "Check SQL syntax."
            )
        fmt = matches.group(1).encode(self._cnx.python_charset)
        values = []

        try:
            stmt = operation.encode(self._cnx.python_charset)
            for params in seq_params:
                tmp = fmt
                prepared = self._cnx.prepare_for_mysql(params)
                if isinstance(prepared, dict):
                    for key, value in prepared.items():
                        tmp = tmp.replace("%({0})s".format(key).encode(), value)
                elif isinstance(prepared, (list, tuple)):
                    psub = _ParamSubstitutor(prepared)
                    tmp = RE_PY_PARAM.sub(psub, tmp)
                    if psub.remaining != 0:
                        raise errors.ProgrammingError(
                            "Not all parameters were used in the SQL statement")
                values.append(tmp)

            if fmt in stmt:
                stmt = stmt.replace(fmt, b','.join(values), 1)
                self._executed = stmt
                return stmt
            return None
        except (UnicodeDecodeError, UnicodeEncodeError) as err:
            raise errors.ProgrammingError(str(err))
        except Exception as err:
            raise errors.InterfaceError(
                "Failed executing the operation; %s" % err)


    def executemany(self, operation, seq_params):
        """Execute the given operation multiple times"""
        if not operation or not seq_params:
            return None

        if not self._cnx:
            raise errors.ProgrammingError("Cursor is not connected")
        self._cnx.handle_unread_result()

        if not isinstance(seq_params, (list, tuple)):
            raise errors.ProgrammingError(
                "Parameters for query must be list or tuple.")

        # Optimize INSERTs by batching them
        if re.match(RE_SQL_INSERT_STMT, operation):
            if not seq_params:
                self._rowcount = 0
                return None
            stmt = self._batch_insert(operation, seq_params)
            if stmt is not None:
                self._executed = stmt
                return self.execute(stmt)

        rowcnt = 0
        try:
            for params in seq_params:
                self.execute(operation, params)
                try:
                    while True:
                        if self._description:
                            rowcnt += len(self._cnx.get_rows()[0])
                        else:
                            rowcnt += self._affected_rows
                        if not self.nextset():
                            break
                except StopIteration:
                    # No more results
                    pass

        except (ValueError, TypeError) as err:
            raise errors.ProgrammingError(
                "Failed executing the operation; {0}".format(err))

        self._rowcount = rowcnt
        return None

    @property
    def description(self):
        """Returns description of columns in a result"""
        return self._description

    @property
    def rowcount(self):
        """Returns the number of rows produced or affected"""
        if self._rowcount == -1:
            return self._affected_rows
        return self._rowcount

    @property
    def lastrowid(self):
        """Returns the value generated for an AUTO_INCREMENT column"""
        return self._insert_id

    def close(self):
        """Close the cursor

        The result will be freed.
        """
        if not self._cnx:
            return False

        self._cnx.handle_unread_result()
        self._warnings = None
        self._cnx = None
        return True

    def callproc(self, procname, args=()):
        """Calls a stored procedure with the given arguments"""
        if not procname or not isinstance(procname, str):
            raise ValueError("procname must be a string")

        if not isinstance(args, (tuple, list)):
            raise ValueError("args must be a sequence")

        argfmt = "@_{name}_arg{index}"
        self._stored_results = []

        try:
            argnames = []
            argtypes = []
            if args:
                for idx, arg in enumerate(args):
                    argname = argfmt.format(name=procname, index=idx + 1)
                    argnames.append(argname)
                    if isinstance(arg, tuple):
                        argtypes.append(" CAST({0} AS {1})".format(argname,
                                                                   arg[1]))
                        self.execute("SET {0}=%s".format(argname), (arg[0],))
                    else:
                        argtypes.append(argname)
                        self.execute("SET {0}=%s".format(argname), (arg,))

            call = "CALL {0}({1})".format(procname, ','.join(argnames))

            result = self._cnx.cmd_query(call, raw=self._raw,
                                         raw_as_string=self._raw_as_string)

            results = []
            while self._cnx.result_set_available:
                result = self._cnx.fetch_eof_columns()
                # pylint: disable=W0212
                if isinstance(self, (CMySQLCursorDict,
                                     CMySQLCursorBufferedDict)):
                    cursor_class = CMySQLCursorBufferedDict
                elif isinstance(self, (CMySQLCursorNamedTuple,
                                       CMySQLCursorBufferedNamedTuple)):
                    cursor_class = CMySQLCursorBufferedNamedTuple
                elif self._raw:
                    cursor_class = CMySQLCursorBufferedRaw
                else:
                    cursor_class = CMySQLCursorBuffered
                cur = cursor_class(self._cnx._get_self())
                cur._executed = "(a result of {0})".format(call)
                cur._handle_result(result)
                # pylint: enable=W0212
                results.append(cur)
                self._cnx.next_result()
            self._stored_results = results
            self._handle_eof()

            if argnames:
                self.reset()
                # Create names aliases to be compatible with namedtuples
                args = [
                    "{} AS {}".format(name, alias) for name, alias in
                    zip(argtypes, [arg.lstrip("@_") for arg in argnames])
                ]
                select = "SELECT {}".format(",".join(args))
                self.execute(select)

                return self.fetchone()
            return tuple()

        except errors.Error:
            raise
        except Exception as err:
            raise errors.InterfaceError(
                "Failed calling stored routine; {0}".format(err))

    def nextset(self):
        """Skip to the next available result set"""
        if not self._cnx.next_result():
            self.reset(free=True)
            return None
        self.reset(free=False)

        if not self._cnx.result_set_available:
            eof = self._cnx.fetch_eof_status()
            self._handle_result(eof)
            raise errors.InterfaceError(errno=CR_NO_RESULT_SET)

        self._handle_result(self._cnx.fetch_eof_columns())
        return True

    def fetchall(self):
        """Returns all rows of a query result set

        Returns a list of tuples.
        """
        self._check_executed()
        if not self._cnx.unread_result:
            return []

        rows = self._cnx.get_rows()
        if self._nextrow and self._nextrow[0]:
            rows[0].insert(0, self._nextrow[0])

        if not rows[0]:
            self._handle_eof()
            return []

        self._rowcount += len(rows[0])
        self._handle_eof()
        #self._cnx.handle_unread_result()
        return rows[0]

    def fetchmany(self, size=1):
        """Returns the next set of rows of a result set"""
        self._check_executed()
        if self._nextrow and self._nextrow[0]:
            rows = [self._nextrow[0]]
            size -= 1
        else:
            rows = []

        if size and self._cnx.unread_result:
            rows.extend(self._cnx.get_rows(size)[0])

        if size:
            if self._cnx.unread_result:
                self._nextrow = self._cnx.get_row()
                if self._nextrow and not self._nextrow[0] and \
                    not self._cnx.more_results:
                    self._cnx.free_result()
            else:
                self._nextrow = (None, None)

        if not rows:
            self._handle_eof()
            return []

        self._rowcount += len(rows)
        return rows

    def fetchone(self):
        """Returns next row of a query result set"""
        self._check_executed()
        row = self._nextrow
        if not row and self._cnx.unread_result:
            row = self._cnx.get_row()

        if row and row[0]:
            self._nextrow = self._cnx.get_row()
            if not self._nextrow[0] and not self._cnx.more_results:
                self._cnx.free_result()
        else:
            self._handle_eof()
            return None
        self._rowcount += 1
        return row[0]

    def __iter__(self):
        """Iteration over the result set

        Iteration over the result set which calls self.fetchone()
        and returns the next row.
        """
        return iter(self.fetchone, None)

    def stored_results(self):
        """Returns an iterator for stored results

        This method returns an iterator over results which are stored when
        callproc() is called. The iterator will provide MySQLCursorBuffered
        instances.

        Returns a iterator.
        """
        for i in range(len(self._stored_results)):
            yield self._stored_results[i]

        self._stored_results = []

    def __next__(self):
        """Iteration over the result set
        Used for iterating over the result set. Calls self.fetchone()
        to get the next row.

        Raises StopIteration when no more rows are available.
        """
        try:
            row = self.fetchone()
        except errors.InterfaceError:
            raise StopIteration
        if not row:
            raise StopIteration
        return row

    @property
    def column_names(self):
        """Returns column names

        This property returns the columns names as a tuple.

        Returns a tuple.
        """
        if not self.description:
            return ()
        return tuple([d[0] for d in self.description])

    @property
    def statement(self):
        """Returns the executed statement

        This property returns the executed statement. When multiple
        statements were executed, the current statement in the iterator
        will be returned.
        """
        try:
            return self._executed.strip().decode('utf8')
        except AttributeError:
            return self._executed.strip()

    @property
    def with_rows(self):
        """Returns whether the cursor could have rows returned

        This property returns True when column descriptions are available
        and possibly also rows, which will need to be fetched.

        Returns True or False.
        """
        if self.description:
            return True
        return False

    def __str__(self):
        fmt = "{class_name}: {stmt}"
        if self._executed:
            try:
                executed = self._executed.decode('utf-8')
            except AttributeError:
                executed = self._executed
            if len(executed) > 40:
                executed = executed[:40] + '..'
        else:
            executed = '(Nothing executed yet)'

        return fmt.format(class_name=self.__class__.__name__, stmt=executed)


class CMySQLCursorBuffered(CMySQLCursor):

    """Cursor using C Extension buffering results"""

    def __init__(self, connection):
        """Initialize"""
        super(CMySQLCursorBuffered, self).__init__(connection)

        self._rows = None
        self._next_row = 0

    def _handle_resultset(self):
        """Handle a result set"""
        self._rows = self._cnx.get_rows()[0]
        self._next_row = 0
        self._rowcount = len(self._rows)
        self._handle_eof()

    def reset(self, free=True):
        """Reset the cursor to default"""
        self._rows = None
        self._next_row = 0
        super(CMySQLCursorBuffered, self).reset(free=free)

    def _fetch_row(self):
        """Returns the next row in the result set

        Returns a tuple or None.
        """
        row = None
        try:
            row = self._rows[self._next_row]
        except IndexError:
            return None
        else:
            self._next_row += 1

        return row

    def fetchall(self):
        self._check_executed()
        res = self._rows[self._next_row:]
        self._next_row = len(self._rows)
        return res

    def fetchmany(self, size=1):
        self._check_executed()
        res = []
        cnt = size or self.arraysize
        while cnt > 0:
            cnt -= 1
            row = self._fetch_row()
            if row:
                res.append(row)
            else:
                break
        return res

    def fetchone(self):
        self._check_executed()
        return self._fetch_row()


class CMySQLCursorRaw(CMySQLCursor):

    """Cursor using C Extension return raw results"""

    _raw = True


class CMySQLCursorBufferedRaw(CMySQLCursorBuffered):

    """Cursor using C Extension buffering raw results"""

    _raw = True


class CMySQLCursorDict(CMySQLCursor):

    """Cursor using C Extension returning rows as dictionaries"""

    _raw = False

    def fetchone(self):
        """Returns all rows of a query result set
        """
        row = super(CMySQLCursorDict, self).fetchone()
        if row:
            return dict(zip(self.column_names, row))
        return None

    def fetchmany(self, size=1):
        """Returns next set of rows as list of dictionaries"""
        res = super(CMySQLCursorDict, self).fetchmany(size=size)
        return [dict(zip(self.column_names, row)) for row in res]

    def fetchall(self):
        """Returns all rows of a query result set as list of dictionaries"""
        res = super(CMySQLCursorDict, self).fetchall()
        return [dict(zip(self.column_names, row)) for row in res]


class CMySQLCursorBufferedDict(CMySQLCursorBuffered):

    """Cursor using C Extension buffering and returning rows as dictionaries"""

    _raw = False

    def _fetch_row(self):
        row = super(CMySQLCursorBufferedDict, self)._fetch_row()
        if row:
            return dict(zip(self.column_names, row))
        return None

    def fetchall(self):
        res = super(CMySQLCursorBufferedDict, self).fetchall()
        return [dict(zip(self.column_names, row)) for row in res]


class CMySQLCursorNamedTuple(CMySQLCursor):

    """Cursor using C Extension returning rows as named tuples"""

    def _handle_resultset(self):
        """Handle a result set"""
        super(CMySQLCursorNamedTuple, self)._handle_resultset()
        # pylint: disable=W0201
        columns = tuple(self.column_names)
        try:
            self.named_tuple = NAMED_TUPLE_CACHE[columns]
        except KeyError:
            self.named_tuple = namedtuple('Row', columns)
            NAMED_TUPLE_CACHE[columns] = self.named_tuple
        # pylint: enable=W0201

    def fetchone(self):
        """Returns all rows of a query result set
        """
        row = super(CMySQLCursorNamedTuple, self).fetchone()
        if row:
            return self.named_tuple(*row)
        return None

    def fetchmany(self, size=1):
        """Returns next set of rows as list of named tuples"""
        res = super(CMySQLCursorNamedTuple, self).fetchmany(size=size)
        if not res:
            return []
        return [self.named_tuple(*res[0])]

    def fetchall(self):
        """Returns all rows of a query result set as list of named tuples"""
        res = super(CMySQLCursorNamedTuple, self).fetchall()
        return [self.named_tuple(*row) for row in res]


class CMySQLCursorBufferedNamedTuple(CMySQLCursorBuffered):

    """Cursor using C Extension buffering and returning rows as named tuples"""

    def _handle_resultset(self):
        super(CMySQLCursorBufferedNamedTuple, self)._handle_resultset()
        # pylint: disable=W0201
        self.named_tuple = namedtuple('Row', self.column_names)
        # pylint: enable=W0201

    def _fetch_row(self):
        row = super(CMySQLCursorBufferedNamedTuple, self)._fetch_row()
        if row:
            return self.named_tuple(*row)
        return None

    def fetchall(self):
        res = super(CMySQLCursorBufferedNamedTuple, self).fetchall()
        return [self.named_tuple(*row) for row in res]


class CMySQLCursorPrepared(CMySQLCursor):

    """Cursor using MySQL Prepared Statements"""

    def __init__(self, connection):
        super(CMySQLCursorPrepared, self).__init__(connection)
        self._rows = None
        self._rowcount = 0
        self._next_row = 0
        self._binary = True
        self._stmt = None

    def _handle_eof(self):
        """Handle EOF packet"""
        self._nextrow = (None, None)
        self._handle_warnings()
        if self._cnx.raise_on_warnings is True and self._warnings:
            raise errors.get_mysql_exception(
                self._warnings[0][1], self._warnings[0][2])

    def _fetch_row(self, raw=False):
        """Returns the next row in the result set

        Returns a tuple or None.
        """
        if not self._stmt or not self._stmt.have_result_set:
            return None
        row = None

        if self._nextrow == (None, None):
            (row, eof) = self._cnx.get_row(
                binary=self._binary, columns=self.description, raw=raw,
                prep_stmt=self._stmt)
        else:
            (row, eof) = self._nextrow

        if row:
            self._nextrow = self._cnx.get_row(
                binary=self._binary, columns=self.description, raw=raw,
                prep_stmt=self._stmt)
            eof = self._nextrow[1]
            if eof is not None:
                self._warning_count = eof["warning_count"]
                self._handle_eof()
            if self._rowcount == -1:
                self._rowcount = 1
            else:
                self._rowcount += 1
        if eof:
            self._warning_count = eof["warning_count"]
            self._handle_eof()

        return row

    def callproc(self, procname, args=None):
        """Calls a stored procedue

        Not supported with CMySQLCursorPrepared.
        """
        raise errors.NotSupportedError()

    def close(self):
        """Close the cursor

        This method will try to deallocate the prepared statement and close
        the cursor.
        """
        if self._stmt:
            self.reset()
            self._cnx.cmd_stmt_close(self._stmt)
            self._stmt = None
        super(CMySQLCursorPrepared, self).close()

    def reset(self, free=True):
        """Resets the prepared statement."""
        if self._stmt:
            self._cnx.cmd_stmt_reset(self._stmt)
        super(CMySQLCursorPrepared, self).reset(free=free)

    def execute(self, operation, params=None, multi=False):  # multi is unused
        """Prepare and execute a MySQL Prepared Statement

        This method will prepare the given operation and execute it using
        the given parameters.

        If the cursor instance already had a prepared statement, it is
        first closed.
        """
        if not operation:
            return

        if not self._cnx or self._cnx.is_closed():
            raise errors.ProgrammingError("Cursor is not connected", 2055)

        self._cnx.handle_unread_result(prepared=True)

        if operation is not self._executed:
            if self._stmt:
                self._cnx.cmd_stmt_close(self._stmt)

            self._executed = operation

            try:
                if not isinstance(operation, bytes):
                    charset = self._cnx.charset
                    if charset == "utf8mb4":
                        charset = "utf8"
                    operation = operation.encode(charset)
            except (UnicodeDecodeError, UnicodeEncodeError) as err:
                raise errors.ProgrammingError(str(err))

            # need to convert %s to ? before sending it to MySQL
            if b"%s" in operation:
                operation = re.sub(RE_SQL_FIND_PARAM, b"?", operation)

            try:
                self._stmt = self._cnx.cmd_stmt_prepare(operation)
            except errors.Error:
                self._executed = None
                self._stmt = None
                raise

        self._cnx.cmd_stmt_reset(self._stmt)

        if self._stmt.param_count > 0 and not params:
            return
        elif params:
            if not isinstance(params, (tuple, list)):
                raise errors.ProgrammingError(
                    errno=1210,
                    msg=f"Incorrect type of argument: {type(params).__name__}({params})"
                    ", it must be of type tuple or list the argument given to "
                    "the prepared statement")
            if self._stmt.param_count != len(params):
                raise errors.ProgrammingError(
                    errno=1210,
                    msg="Incorrect number of arguments executing prepared "
                        "statement")

        if params is None:
            params = ()
        res = self._cnx.cmd_stmt_execute(self._stmt, *params)
        if res:
            self._handle_result(res)

    def executemany(self, operation, seq_params):
        """Prepare and execute a MySQL Prepared Statement many times

        This method will prepare the given operation and execute with each
        tuple found the list seq_params.

        If the cursor instance already had a prepared statement, it is
        first closed.
        """
        rowcnt = 0
        try:
            for params in seq_params:
                self.execute(operation, params)
                if self.with_rows:
                    self.fetchall()
                rowcnt += self._rowcount
        except (ValueError, TypeError) as err:
            raise errors.InterfaceError(
                "Failed executing the operation; {error}".format(error=err))
        except:
            # Raise whatever execute() raises
            raise
        self._rowcount = rowcnt

    def fetchone(self):
        """Returns next row of a query result set

        Returns a tuple or None.
        """
        self._check_executed()
        return self._fetch_row() or None

    def fetchmany(self, size=None):
        """Returns the next set of rows of a result set

        Returns a list of tuples.
        """
        self._check_executed()
        res = []
        cnt = size or self.arraysize
        while cnt > 0 and self._stmt.have_result_set:
            cnt -= 1
            row = self._fetch_row()
            if row:
                res.append(row)
        return res

    def fetchall(self):
        """Returns all rows of a query result set

        Returns a list of tuples.
        """
        self._check_executed()
        if not self._stmt.have_result_set:
            return []

        rows = self._cnx.get_rows(prep_stmt=self._stmt)
        if self._nextrow and self._nextrow[0]:
            rows[0].insert(0, self._nextrow[0])

        if not rows[0]:
            self._handle_eof()
            return []

        self._rowcount += len(rows[0])
        self._handle_eof()
        return rows[0]

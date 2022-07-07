# Copyright (c) 2009, 2021, Oracle and/or its affiliates.
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

"""Cursor classes
"""

from collections import namedtuple
import re
import weakref

from . import errors
from .abstracts import MySQLCursorAbstract, NAMED_TUPLE_CACHE
from .constants import ServerFlag

SQL_COMMENT = r"\/\*.*?\*\/"
RE_SQL_COMMENT = re.compile(
    r'''({0})|(["'`][^"'`]*?({0})[^"'`]*?["'`])'''.format(SQL_COMMENT),
    re.I | re.M | re.S)
RE_SQL_ON_DUPLICATE = re.compile(
    r'''\s*ON\s+DUPLICATE\s+KEY(?:[^"'`]*["'`][^"'`]*["'`])*[^"'`]*$''',
    re.I | re.M | re.S)
RE_SQL_INSERT_STMT = re.compile(
    r"({0}|\s)*INSERT({0}|\s)*INTO\s+[`'\"]?.+[`'\"]?(?:\.[`'\"]?.+[`'\"]?)"
    r"{{0,2}}\s+VALUES\s*\(.+(?:\s*,.+)*\)".format(SQL_COMMENT),
    re.I | re.M | re.S)
RE_SQL_INSERT_VALUES = re.compile(r'.*VALUES\s*(\(.*\)).*', re.I | re.M | re.S)
RE_PY_PARAM = re.compile(b'(%s)')
RE_PY_MAPPING_PARAM = re.compile(
    br'''
    %
    \((?P<mapping_key>[^)]+)\)
    (?P<conversion_type>[diouxXeEfFgGcrs%])
    ''',
    re.X
)
RE_SQL_SPLIT_STMTS = re.compile(
    b''';(?=(?:[^"'`]*["'`][^"'`]*["'`])*[^"'`]*$)''')
RE_SQL_FIND_PARAM = re.compile(
    b'''%s(?=(?:[^"'`]*["'`][^"'`]*["'`])*[^"'`]*$)''')

ERR_NO_RESULT_TO_FETCH = "No result set to fetch from"

MAX_RESULTS = 4294967295

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
            return bytes(self.params[index])
        except IndexError:
            raise errors.ProgrammingError(
                "Not enough parameters for the SQL statement")

    @property
    def remaining(self):
        """Returns number of parameters remaining to be substituted"""
        return len(self.params) - self.index


def _bytestr_format_dict(bytestr, value_dict):
    """
    >>> _bytestr_format_dict(b'%(a)s', {b'a': b'foobar'})
    b'foobar
    >>> _bytestr_format_dict(b'%%(a)s', {b'a': b'foobar'})
    b'%%(a)s'
    >>> _bytestr_format_dict(b'%%%(a)s', {b'a': b'foobar'})
    b'%%foobar'
    >>> _bytestr_format_dict(b'%(x)s %(y)s',
    ...                      {b'x': b'x=%(y)s', b'y': b'y=%(x)s'})
    b'x=%(y)s y=%(x)s'
    """
    def replace(matchobj):
        """Replace pattern."""
        value = None
        groups = matchobj.groupdict()
        if groups["conversion_type"] == b"%":
            value = b"%"
        if groups["conversion_type"] == b"s":
            key = groups["mapping_key"]
            value = value_dict[key]
        if value is None:
            raise ValueError("Unsupported conversion_type: {0}"
                             "".format(groups["conversion_type"]))
        return value

    stmt = RE_PY_MAPPING_PARAM.sub(replace, bytestr)
    return stmt


class CursorBase(MySQLCursorAbstract):
    """
    Base for defining MySQLCursor. This class is a skeleton and defines
    methods and members as required for the Python Database API
    Specification v2.0.

    It's better to inherite from MySQLCursor.
    """

    _raw = False

    def __init__(self):
        self._description = None
        self._rowcount = -1
        self._last_insert_id = None
        self.arraysize = 1
        super(CursorBase, self).__init__()

    def callproc(self, procname, args=()):
        """Calls a stored procedue with the given arguments

        The arguments will be set during this session, meaning
        they will be called like  _<procname>__arg<nr> where
        <nr> is an enumeration (+1) of the arguments.

        Coding Example:
          1) Definining the Stored Routine in MySQL:
          CREATE PROCEDURE multiply(IN pFac1 INT, IN pFac2 INT, OUT pProd INT)
          BEGIN
            SET pProd := pFac1 * pFac2;
          END

          2) Executing in Python:
          args = (5,5,0) # 0 is to hold pprod
          cursor.callproc('multiply', args)
          print(cursor.fetchone())

        Does not return a value, but a result set will be
        available when the CALL-statement execute successfully.
        Raises exceptions when something is wrong.
        """
        pass

    def close(self):
        """Close the cursor."""
        pass

    def execute(self, operation, params=(), multi=False):
        """Executes the given operation

        Executes the given operation substituting any markers with
        the given parameters.

        For example, getting all rows where id is 5:
          cursor.execute("SELECT * FROM t1 WHERE id = %s", (5,))

        The multi argument should be set to True when executing multiple
        statements in one operation. If not set and multiple results are
        found, an InterfaceError will be raised.

        If warnings where generated, and connection.get_warnings is True, then
        self._warnings will be a list containing these warnings.

        Returns an iterator when multi is True, otherwise None.
        """
        pass

    def executemany(self, operation, seq_params):
        """Execute the given operation multiple times

        The executemany() method will execute the operation iterating
        over the list of parameters in seq_params.

        Example: Inserting 3 new employees and their phone number

        data = [
            ('Jane','555-001'),
            ('Joe', '555-001'),
            ('John', '555-003')
            ]
        stmt = "INSERT INTO employees (name, phone) VALUES ('%s','%s')"
        cursor.executemany(stmt, data)

        INSERT statements are optimized by batching the data, that is
        using the MySQL multiple rows syntax.

        Results are discarded. If they are needed, consider looping over
        data using the execute() method.
        """
        pass

    def fetchone(self):
        """Returns next row of a query result set

        Returns a tuple or None.
        """
        pass

    def fetchmany(self, size=1):
        """Returns the next set of rows of a query result, returning a
        list of tuples. When no more rows are available, it returns an
        empty list.

        The number of rows returned can be specified using the size argument,
        which defaults to one
        """
        pass

    def fetchall(self):
        """Returns all rows of a query result set

        Returns a list of tuples.
        """
        pass

    def nextset(self):
        """Not Implemented."""
        pass

    def setinputsizes(self, sizes):
        """Not Implemented."""
        pass

    def setoutputsize(self, size, column=None):
        """Not Implemented."""
        pass

    def reset(self, free=True):
        """Reset the cursor to default"""
        pass

    @property
    def description(self):
        """Returns description of columns in a result

        This property returns a list of tuples describing the columns in
        in a result set. A tuple is described as follows::

                (column_name,
                 type,
                 None,
                 None,
                 None,
                 None,
                 null_ok,
                 column_flags)  # Addition to PEP-249 specs

        Returns a list of tuples.
        """
        return self._description

    @property
    def rowcount(self):
        """Returns the number of rows produced or affected

        This property returns the number of rows produced by queries
        such as a SELECT, or affected rows when executing DML statements
        like INSERT or UPDATE.

        Note that for non-buffered cursors it is impossible to know the
        number of rows produced before having fetched them all. For those,
        the number of rows will be -1 right after execution, and
        incremented when fetching rows.

        Returns an integer.
        """
        return self._rowcount

    @property
    def lastrowid(self):
        """Returns the value generated for an AUTO_INCREMENT column

        Returns the value generated for an AUTO_INCREMENT column by
        the previous INSERT or UPDATE statement or None when there is
        no such value available.

        Returns a long value or None.
        """
        return self._last_insert_id


class MySQLCursor(CursorBase):
    """Default cursor for interacting with MySQL

    This cursor will execute statements and handle the result. It will
    not automatically fetch all rows.

    MySQLCursor should be inherited whenever other functionallity is
    required. An example would to change the fetch* member functions
    to return dictionaries instead of lists of values.

    Implements the Python Database API Specification v2.0 (PEP-249)
    """
    def __init__(self, connection=None):
        CursorBase.__init__(self)
        self._connection = None
        self._stored_results = []
        self._nextrow = (None, None)
        self._warnings = None
        self._warning_count = 0
        self._executed = None
        self._executed_list = []
        self._binary = False

        if connection is not None:
            self._set_connection(connection)

    def __iter__(self):
        """
        Iteration over the result set which calls self.fetchone()
        and returns the next row.
        """
        return iter(self.fetchone, None)

    def _set_connection(self, connection):
        """Set the connection"""
        try:
            self._connection = weakref.proxy(connection)
            self._connection.is_connected()
        except (AttributeError, TypeError):
            raise errors.InterfaceError(errno=2048)

    def _reset_result(self):
        """Reset the cursor to default"""
        self._rowcount = -1
        self._nextrow = (None, None)
        self._stored_results = []
        self._warnings = None
        self._warning_count = 0
        self._description = None
        self._executed = None
        self._executed_list = []
        self.reset()

    def _have_unread_result(self):
        """Check whether there is an unread result"""
        try:
            return self._connection.unread_result
        except AttributeError:
            return False

    def _check_executed(self):
        """Check if the statement has been executed.

        Raises an error if the statement has not been executed.
        """
        if self._executed is None:
            raise errors.InterfaceError(ERR_NO_RESULT_TO_FETCH)

    def next(self):
        """Used for iterating over the result set."""
        return self.__next__()

    def __next__(self):
        """
        Used for iterating over the result set. Calles self.fetchone()
        to get the next row.
        """
        try:
            row = self.fetchone()
        except errors.InterfaceError:
            raise StopIteration
        if not row:
            raise StopIteration
        return row

    def close(self):
        """Close the cursor

        Returns True when successful, otherwise False.
        """
        if self._connection is None:
            return False

        self._connection.handle_unread_result()
        self._reset_result()
        self._connection = None

        return True

    def _process_params_dict(self, params):
        """Process query parameters given as dictionary"""
        try:
            to_mysql = self._connection.converter.to_mysql
            escape = self._connection.converter.escape
            quote = self._connection.converter.quote
            res = {}
            for key, value in list(params.items()):
                conv = value
                conv = to_mysql(conv)
                conv = escape(conv)
                conv = quote(conv)
                res[key.encode()] = conv
        except Exception as err:
            raise errors.ProgrammingError(
                "Failed processing pyformat-parameters; %s" % err)
        else:
            return res

    def _process_params(self, params):
        """Process query parameters."""
        try:
            res = params

            to_mysql = self._connection.converter.to_mysql
            escape = self._connection.converter.escape
            quote = self._connection.converter.quote

            res = [to_mysql(i) for i in res]
            res = [escape(i) for i in res]
            res = [quote(i) for i in res]
        except Exception as err:
            raise errors.ProgrammingError(
                "Failed processing format-parameters; %s" % err)
        else:
            return tuple(res)

    def _handle_noresultset(self, res):
        """Handles result of execute() when there is no result set
        """
        try:
            self._rowcount = res['affected_rows']
            self._last_insert_id = res['insert_id']
            self._warning_count = res['warning_count']
        except (KeyError, TypeError) as err:
            raise errors.ProgrammingError(
                "Failed handling non-resultset; {0}".format(err))

        self._handle_warnings()
        if self._connection.raise_on_warnings is True and self._warnings:
            raise errors.get_mysql_exception(
                self._warnings[0][1], self._warnings[0][2])

    def _handle_resultset(self):
        """Handles result set

        This method handles the result set and is called after reading
        and storing column information in _handle_result(). For non-buffering
        cursors, this method is usually doing nothing.
        """
        pass

    def _handle_result(self, result):
        """
        Handle the result after a command was send. The result can be either
        an OK-packet or a dictionary containing column/eof information.

        Raises InterfaceError when result is not a dict() or result is
        invalid.
        """
        if not isinstance(result, dict):
            raise errors.InterfaceError('Result was not a dict()')

        if 'columns' in result:
            # Weak test, must be column/eof information
            self._description = result['columns']
            self._connection.unread_result = True
            self._handle_resultset()
        elif 'affected_rows' in result:
            # Weak test, must be an OK-packet
            self._connection.unread_result = False
            self._handle_noresultset(result)
        else:
            raise errors.InterfaceError('Invalid result')

    def _execute_iter(self, query_iter):
        """Generator returns MySQLCursor objects for multiple statements

        This method is only used when multiple statements are executed
        by the execute() method. It uses zip() to make an iterator from the
        given query_iter (result of MySQLConnection.cmd_query_iter()) and
        the list of statements that were executed.
        """
        executed_list = RE_SQL_SPLIT_STMTS.split(self._executed)

        i = 0
        while True:
            try:
                result = next(query_iter)
                self._reset_result()
                self._handle_result(result)
                try:
                    self._executed = executed_list[i].strip()
                    i += 1
                except IndexError:
                    self._executed = executed_list[0]

                yield self
            except StopIteration:
                return

    def execute(self, operation, params=None, multi=False):
        """Executes the given operation

        Executes the given operation substituting any markers with
        the given parameters.

        For example, getting all rows where id is 5:
          cursor.execute("SELECT * FROM t1 WHERE id = %s", (5,))

        The multi argument should be set to True when executing multiple
        statements in one operation. If not set and multiple results are
        found, an InterfaceError will be raised.

        If warnings where generated, and connection.get_warnings is True, then
        self._warnings will be a list containing these warnings.

        Returns an iterator when multi is True, otherwise None.
        """
        if not operation:
            return None

        if not self._connection:
            raise errors.ProgrammingError("Cursor is not connected")

        self._connection.handle_unread_result()

        self._reset_result()
        stmt = ''

        try:
            if not isinstance(operation, (bytes, bytearray)):
                stmt = operation.encode(self._connection.python_charset)
            else:
                stmt = operation
        except (UnicodeDecodeError, UnicodeEncodeError) as err:
            raise errors.ProgrammingError(str(err))

        if params:
            if isinstance(params, dict):
                stmt = _bytestr_format_dict(
                    stmt, self._process_params_dict(params))
            elif isinstance(params, (list, tuple)):
                psub = _ParamSubstitutor(self._process_params(params))
                stmt = RE_PY_PARAM.sub(psub, stmt)
                if psub.remaining != 0:
                    raise errors.ProgrammingError(
                        "Not all parameters were used in the SQL statement")
            else:
                raise errors.ProgrammingError(
                    f"Could not process parameters: {type(params).__name__}({params}),"
                    " it must be of type list, tuple or dict")

        self._executed = stmt
        if multi:
            self._executed_list = []
            return self._execute_iter(self._connection.cmd_query_iter(stmt))

        try:
            self._handle_result(self._connection.cmd_query(stmt))
        except errors.InterfaceError:
            if self._connection._have_next_result:  # pylint: disable=W0212
                raise errors.InterfaceError(
                    "Use multi=True when executing multiple statements")
            raise
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
        fmt = matches.group(1).encode(self._connection.python_charset)
        values = []

        try:
            stmt = operation.encode(self._connection.python_charset)
            for params in seq_params:
                tmp = fmt
                if isinstance(params, dict):
                    tmp = _bytestr_format_dict(
                        tmp, self._process_params_dict(params))
                else:
                    psub = _ParamSubstitutor(self._process_params(params))
                    tmp = RE_PY_PARAM.sub(psub, tmp)
                    if psub.remaining != 0:
                        raise errors.ProgrammingError(
                            "Not all parameters were used in the SQL statement")
                    #for p in self._process_params(params):
                    #    tmp = tmp.replace(b'%s',p,1)
                values.append(tmp)
            if fmt in stmt:
                stmt = stmt.replace(fmt, b','.join(values), 1)
                self._executed = stmt
                return stmt
            return None
        except (UnicodeDecodeError, UnicodeEncodeError) as err:
            raise errors.ProgrammingError(str(err))
        except errors.Error:
            raise
        except Exception as err:
            raise errors.InterfaceError(
                "Failed executing the operation; %s" % err)

    def executemany(self, operation, seq_params):
        """Execute the given operation multiple times

        The executemany() method will execute the operation iterating
        over the list of parameters in seq_params.

        Example: Inserting 3 new employees and their phone number

        data = [
            ('Jane','555-001'),
            ('Joe', '555-001'),
            ('John', '555-003')
            ]
        stmt = "INSERT INTO employees (name, phone) VALUES ('%s','%s)"
        cursor.executemany(stmt, data)

        INSERT statements are optimized by batching the data, that is
        using the MySQL multiple rows syntax.

        Results are discarded. If they are needed, consider looping over
        data using the execute() method.
        """
        if not operation or not seq_params:
            return None
        self._connection.handle_unread_result()

        try:
            _ = iter(seq_params)
        except TypeError:
            raise errors.ProgrammingError(
                "Parameters for query must be an Iterable.")

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
                if self.with_rows and self._have_unread_result():
                    self.fetchall()
                rowcnt += self._rowcount
        except (ValueError, TypeError) as err:
            raise errors.InterfaceError(
                "Failed executing the operation; {0}".format(err))
        except:
            # Raise whatever execute() raises
            raise
        self._rowcount = rowcnt
        return None

    def stored_results(self):
        """Returns an iterator for stored results

        This method returns an iterator over results which are stored when
        callproc() is called. The iterator will provide MySQLCursorBuffered
        instances.

        Returns a iterator.
        """
        return iter(self._stored_results)

    def callproc(self, procname, args=()):
        """Calls a stored procedure with the given arguments

        The arguments will be set during this session, meaning
        they will be called like  _<procname>__arg<nr> where
        <nr> is an enumeration (+1) of the arguments.

        Coding Example:
          1) Defining the Stored Routine in MySQL:
          CREATE PROCEDURE multiply(IN pFac1 INT, IN pFac2 INT, OUT pProd INT)
          BEGIN
            SET pProd := pFac1 * pFac2;
          END

          2) Executing in Python:
          args = (5, 5, 0)  # 0 is to hold pprod
          cursor.callproc('multiply', args)
          print(cursor.fetchone())

        For OUT and INOUT parameters the user should provide the
        type of the parameter as well. The argument should be a
        tuple with first item as the value of the parameter to pass
        and second argument the type of the argument.

        In the above example, one can call callproc method like:
          args = (5, 5, (0, 'INT'))
          cursor.callproc('multiply', args)

        The type of the argument given in the tuple will be used by
        the MySQL CAST function to convert the values in the corresponding
        MySQL type (See CAST in MySQL Reference for more information)

        Does not return a value, but a result set will be
        available when the CALL-statement execute successfully.
        Raises exceptions when something is wrong.
        """
        if not procname or not isinstance(procname, str):
            raise ValueError("procname must be a string")

        if not isinstance(args, (tuple, list)):
            raise ValueError("args must be a sequence")

        argfmt = "@_{name}_arg{index}"
        self._stored_results = []

        results = []
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

            # pylint: disable=W0212
            # We disable consuming results temporary to make sure we
            # getting all results
            can_consume_results = self._connection._consume_results
            for result in self._connection.cmd_query_iter(call):
                self._connection._consume_results = False
                if isinstance(self, (MySQLCursorDict,
                                     MySQLCursorBufferedDict)):
                    cursor_class = MySQLCursorBufferedDict
                elif isinstance(self, (MySQLCursorNamedTuple,
                                       MySQLCursorBufferedNamedTuple)):
                    cursor_class = MySQLCursorBufferedNamedTuple
                elif self._raw:
                    cursor_class = MySQLCursorBufferedRaw
                else:
                    cursor_class = MySQLCursorBuffered
                tmp = cursor_class(self._connection._get_self())
                tmp._executed = "(a result of {0})".format(call)
                tmp._handle_result(result)
                if tmp._warnings is not None:
                    self._warnings = tmp._warnings
                if 'columns' in result:
                    results.append(tmp)
            self._connection._consume_results = can_consume_results
            # pylint: enable=W0212

            if argnames:
                # Create names aliases to be compatible with namedtuples
                args = [
                    "{} AS {}".format(name, alias) for name, alias in
                    zip(argtypes, [arg.lstrip("@_") for arg in argnames])
                ]
                select = "SELECT {}".format(",".join(args))
                self.execute(select)
                self._stored_results = results
                return self.fetchone()

            self._stored_results = results
            return ()

        except errors.Error:
            raise
        except Exception as err:
            raise errors.InterfaceError(
                "Failed calling stored routine; {0}".format(err))

    def getlastrowid(self):
        """Returns the value generated for an AUTO_INCREMENT column

        Returns the value generated for an AUTO_INCREMENT column by
        the previous INSERT or UPDATE statement.

        Returns a long value or None.
        """
        return self._last_insert_id

    def _fetch_warnings(self):
        """
        Fetch warnings doing a SHOW WARNINGS. Can be called after getting
        the result.

        Returns a result set or None when there were no warnings.
        """
        res = []
        try:
            cur = self._connection.cursor(raw=False)
            cur.execute("SHOW WARNINGS")
            res = cur.fetchall()
            cur.close()
        except Exception as err:
            raise errors.InterfaceError(
                "Failed getting warnings; %s" % err)

        if res:
            return res

        return None

    def _handle_warnings(self):
        """Handle possible warnings after all results are consumed"""
        if self._connection.get_warnings is True and self._warning_count:
            self._warnings = self._fetch_warnings()

    def _handle_eof(self, eof):
        """Handle EOF packet"""
        self._connection.unread_result = False
        self._nextrow = (None, None)
        self._warning_count = eof['warning_count']
        self._handle_warnings()
        if self._connection.raise_on_warnings is True and self._warnings:
            raise errors.get_mysql_exception(
                self._warnings[0][1], self._warnings[0][2])

    def _fetch_row(self, raw=False):
        """Returns the next row in the result set

        Returns a tuple or None.
        """
        if not self._have_unread_result():
            return None
        row = None

        if self._nextrow == (None, None):
            (row, eof) = self._connection.get_row(
                binary=self._binary, columns=self.description, raw=raw)
        else:
            (row, eof) = self._nextrow

        if row:
            self._nextrow = self._connection.get_row(
                binary=self._binary, columns=self.description, raw=raw)
            eof = self._nextrow[1]
            if eof is not None:
                self._handle_eof(eof)
            if self._rowcount == -1:
                self._rowcount = 1
            else:
                self._rowcount += 1
        if eof:
            self._handle_eof(eof)

        return row

    def fetchone(self):
        """Returns next row of a query result set

        Returns a tuple or None.
        """
        self._check_executed()
        return self._fetch_row()

    def fetchmany(self, size=None):
        self._check_executed()
        res = []
        cnt = (size or self.arraysize)
        while cnt > 0 and self._have_unread_result():
            cnt -= 1
            row = self.fetchone()
            if row:
                res.append(row)
        return res

    def fetchall(self):
        self._check_executed()
        if not self._have_unread_result():
            return []

        (rows, eof) = self._connection.get_rows()
        if self._nextrow[0]:
            rows.insert(0, self._nextrow[0])

        self._handle_eof(eof)
        rowcount = len(rows)
        if rowcount >= 0 and self._rowcount == -1:
            self._rowcount = 0
        self._rowcount += rowcount
        return rows

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
        if self._executed is None:
            return None
        try:
            return self._executed.strip().decode('utf-8')
        except (AttributeError, UnicodeDecodeError):
            return self._executed.strip()

    @property
    def with_rows(self):
        """Returns whether the cursor could have rows returned

        This property returns True when column descriptions are available
        and possibly also rows, which will need to be fetched.

        Returns True or False.
        """
        if not self.description:
            return False
        return True

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


class MySQLCursorBuffered(MySQLCursor):
    """Cursor which fetches rows within execute()"""

    def __init__(self, connection=None):
        MySQLCursor.__init__(self, connection)
        self._rows = None
        self._next_row = 0

    def _handle_resultset(self):
        (self._rows, eof) = self._connection.get_rows()
        self._rowcount = len(self._rows)
        self._handle_eof(eof)
        self._next_row = 0
        try:
            self._connection.unread_result = False
        except:
            pass

    def reset(self, free=True):
        self._rows = None

    def _fetch_row(self, raw=False):
        row = None
        try:
            row = self._rows[self._next_row]
        except:
            return None
        else:
            self._next_row += 1
            return row
        return None

    def fetchone(self):
        """Returns next row of a query result set

        Returns a tuple or None.
        """
        self._check_executed()
        return self._fetch_row()

    def fetchall(self):
        if self._executed is None or self._rows is None:
            raise errors.InterfaceError(ERR_NO_RESULT_TO_FETCH)
        res = []
        res = self._rows[self._next_row:]
        self._next_row = len(self._rows)
        return res

    def fetchmany(self, size=None):
        self._check_executed()
        res = []
        cnt = (size or self.arraysize)
        while cnt > 0:
            cnt -= 1
            row = self.fetchone()
            if row:
                res.append(row)

        return res

    @property
    def with_rows(self):
        return self._rows is not None


class MySQLCursorRaw(MySQLCursor):
    """
    Skips conversion from MySQL datatypes to Python types when fetching rows.
    """

    _raw = True

    def fetchone(self):
        self._check_executed()
        return self._fetch_row(raw=True)

    def fetchall(self):
        self._check_executed()
        if not self._have_unread_result():
            return []
        (rows, eof) = self._connection.get_rows(raw=True)
        if self._nextrow[0]:
            rows.insert(0, self._nextrow[0])
        self._handle_eof(eof)
        rowcount = len(rows)
        if rowcount >= 0 and self._rowcount == -1:
            self._rowcount = 0
        self._rowcount += rowcount
        return rows


class MySQLCursorBufferedRaw(MySQLCursorBuffered):
    """
    Cursor which skips conversion from MySQL datatypes to Python types when
    fetching rows and fetches rows within execute().
    """

    _raw = True

    def _handle_resultset(self):
        (self._rows, eof) = self._connection.get_rows(raw=self._raw)
        self._rowcount = len(self._rows)
        self._handle_eof(eof)
        self._next_row = 0
        try:
            self._connection.unread_result = False
        except:
            pass

    def fetchone(self):
        self._check_executed()
        return self._fetch_row()

    def fetchall(self):
        self._check_executed()
        return [r for r in self._rows[self._next_row:]]

    @property
    def with_rows(self):
        return self._rows is not None


class MySQLCursorPrepared(MySQLCursor):
    """Cursor using MySQL Prepared Statements
    """
    def __init__(self, connection=None):
        super(MySQLCursorPrepared, self).__init__(connection)
        self._rows = None
        self._next_row = 0
        self._prepared = None
        self._binary = True
        self._have_result = None
        self._last_row_sent = False
        self._cursor_exists = False

    def reset(self, free=True):
        if self._prepared:
            try:
                self._connection.cmd_stmt_close(self._prepared['statement_id'])
            except errors.Error:
                # We tried to deallocate, but it's OK when we fail.
                pass
            self._prepared = None
        self._last_row_sent = False
        self._cursor_exists = False

    def _handle_noresultset(self, res):
        self._handle_server_status(res.get('status_flag',
                                           res.get('server_status', 0)))
        super(MySQLCursorPrepared, self)._handle_noresultset(res)

    def _handle_server_status(self, flags):
        """Check for SERVER_STATUS_CURSOR_EXISTS and
           SERVER_STATUS_LAST_ROW_SENT flags set by the server.
        """
        self._cursor_exists = flags & ServerFlag.STATUS_CURSOR_EXISTS != 0
        self._last_row_sent = flags & ServerFlag.STATUS_LAST_ROW_SENT != 0

    def _handle_eof(self, eof):
        self._handle_server_status(eof.get('status_flag',
                                           eof.get('server_status', 0)))
        super(MySQLCursorPrepared, self)._handle_eof(eof)

    def callproc(self, procname, args=()):
        """Calls a stored procedue

        Not supported with MySQLCursorPrepared.
        """
        raise errors.NotSupportedError()

    def close(self):
        """Close the cursor

        This method will try to deallocate the prepared statement and close
        the cursor.
        """
        self.reset()
        super(MySQLCursorPrepared, self).close()

    def _row_to_python(self, rowdata, desc=None):
        """Convert row data from MySQL to Python types

        The conversion is done while reading binary data in the
        protocol module.
        """
        pass

    def _handle_result(self, result):
        """Handle result after execution"""
        if isinstance(result, dict):
            self._connection.unread_result = False
            self._have_result = False
            self._handle_noresultset(result)
        else:
            self._description = result[1]
            self._connection.unread_result = True
            self._have_result = True

            if 'status_flag' in result[2]:
                self._handle_server_status(result[2]['status_flag'])
            elif 'server_status' in result[2]:
                self._handle_server_status(result[2]['server_status'])

    def execute(self, operation, params=None, multi=False):  # multi is unused
        """Prepare and execute a MySQL Prepared Statement

        This method will prepare the given operation and execute it using
        the optionally given parameters.

        If the cursor instance already had a prepared statement, it is
        first closed.
        """
        if operation is not self._executed:
            if self._prepared:
                self._connection.cmd_stmt_close(self._prepared['statement_id'])

            self._executed = operation
            try:
                if not isinstance(operation, bytes):
                    charset = self._connection.charset
                    if charset == 'utf8mb4':
                        charset = 'utf8'
                    operation = operation.encode(charset)
            except (UnicodeDecodeError, UnicodeEncodeError) as err:
                raise errors.ProgrammingError(str(err))

            # need to convert %s to ? before sending it to MySQL
            if b'%s' in operation:
                operation = re.sub(RE_SQL_FIND_PARAM, b'?', operation)

            try:
                self._prepared = self._connection.cmd_stmt_prepare(operation)
            except errors.Error:
                self._executed = None
                raise

        self._connection.cmd_stmt_reset(self._prepared['statement_id'])

        if self._prepared['parameters'] and not params:
            return
        elif params:
            if not isinstance(params, (tuple, list)):
                raise errors.ProgrammingError(
                    errno=1210,
                    msg=f"Incorrect type of argument: {type(params).__name__}({params})"
                    ", it must be of type tuple or list the argument given to "
                    "the prepared statement")
            if len(self._prepared['parameters']) != len(params):
                raise errors.ProgrammingError(
                    errno=1210,
                    msg="Incorrect number of arguments " \
                        "executing prepared statement")

        if params is None:
            params = ()
        res = self._connection.cmd_stmt_execute(
            self._prepared['statement_id'],
            data=params,
            parameters=self._prepared['parameters'])
        self._handle_result(res)

    def executemany(self, operation, seq_params):
        """Prepare and execute a MySQL Prepared Statement many times

        This method will prepare the given operation and execute with each
        tuple found the list seq_params.

        If the cursor instance already had a prepared statement, it is
        first closed.

        executemany() simply calls execute().
        """
        rowcnt = 0
        try:
            for params in seq_params:
                self.execute(operation, params)
                if self.with_rows and self._have_unread_result():
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
        if self._cursor_exists:
            self._connection.cmd_stmt_fetch(self._prepared['statement_id'])
        return self._fetch_row() or None

    def fetchmany(self, size=None):
        self._check_executed()
        res = []
        cnt = (size or self.arraysize)
        while cnt > 0 and self._have_unread_result():
            cnt -= 1
            row = self._fetch_row()
            if row:
                res.append(row)
        return res

    def fetchall(self):
        self._check_executed()
        rows = []
        if self._nextrow[0]:
            rows.append(self._nextrow[0])
        while self._have_unread_result():
            if self._cursor_exists:
                self._connection.cmd_stmt_fetch(
                    self._prepared['statement_id'], MAX_RESULTS)
            (tmp, eof) = self._connection.get_rows(
                binary=self._binary, columns=self.description)
            rows.extend(tmp)
            self._handle_eof(eof)
        self._rowcount = len(rows)
        return rows


class MySQLCursorDict(MySQLCursor):
    """
    Cursor fetching rows as dictionaries.

    The fetch methods of this class will return dictionaries instead of tuples.
    Each row is a dictionary that looks like:
        row = {
            "col1": value1,
            "col2": value2
        }
    """
    def _row_to_python(self, rowdata, desc=None):
        """Convert a MySQL text result row to Python types

        Returns a dictionary.
        """
        row = rowdata

        if row:
            return dict(zip(self.column_names, row))

        return None

    def fetchone(self):
        """Returns next row of a query result set
        """
        self._check_executed()
        row = self._fetch_row()
        if row:
            return self._row_to_python(row, self.description)
        return None

    def fetchall(self):
        """Returns all rows of a query result set
        """
        self._check_executed()
        if not self._have_unread_result():
            return []

        (rows, eof) = self._connection.get_rows()
        if self._nextrow[0]:
            rows.insert(0, self._nextrow[0])
        res = []
        for row in rows:
            res.append(self._row_to_python(row, self.description))
        self._handle_eof(eof)
        rowcount = len(rows)
        if rowcount >= 0 and self._rowcount == -1:
            self._rowcount = 0
        self._rowcount += rowcount
        return res


class MySQLCursorNamedTuple(MySQLCursor):
    """
    Cursor fetching rows as named tuple.

    The fetch methods of this class will return namedtuples instead of tuples.
    Each row is returned as a namedtuple and the values can be accessed as:
    row.col1, row.col2
    """
    def _row_to_python(self, rowdata, desc=None):
        """Convert a MySQL text result row to Python types

        Returns a named tuple.
        """
        row = rowdata

        if row:
            # pylint: disable=W0201
            columns = tuple(self.column_names)
            try:
                named_tuple = NAMED_TUPLE_CACHE[columns]
            except KeyError:
                named_tuple = namedtuple('Row', columns)
                NAMED_TUPLE_CACHE[columns] = named_tuple
            # pylint: enable=W0201
            return named_tuple(*row)
        return None

    def fetchone(self):
        """Returns next row of a query result set
        """
        self._check_executed()
        row = self._fetch_row()
        if row:
            if hasattr(self._connection, 'converter'):
                return self._row_to_python(row, self.description)
            return row
        return None

    def fetchall(self):
        """Returns all rows of a query result set
        """
        self._check_executed()
        if not self._have_unread_result():
            return []

        (rows, eof) = self._connection.get_rows()
        if self._nextrow[0]:
            rows.insert(0, self._nextrow[0])
        res = [self._row_to_python(row, self.description)
               for row in rows]

        self._handle_eof(eof)
        rowcount = len(rows)
        if rowcount >= 0 and self._rowcount == -1:
            self._rowcount = 0
        self._rowcount += rowcount
        return res


class MySQLCursorBufferedDict(MySQLCursorDict, MySQLCursorBuffered):
    """
    Buffered Cursor fetching rows as dictionaries.
    """
    def fetchone(self):
        """Returns next row of a query result set
        """
        self._check_executed()
        row = self._fetch_row()
        if row:
            return self._row_to_python(row, self.description)
        return None

    def fetchall(self):
        """Returns all rows of a query result set
        """
        if self._executed is None or self._rows is None:
            raise errors.InterfaceError(ERR_NO_RESULT_TO_FETCH)
        res = []
        for row in self._rows[self._next_row:]:
            res.append(self._row_to_python(
                row, self.description))
        self._next_row = len(self._rows)
        return res


class MySQLCursorBufferedNamedTuple(MySQLCursorNamedTuple, MySQLCursorBuffered):
    """
    Buffered Cursor fetching rows as named tuple.
    """
    def fetchone(self):
        """Returns next row of a query result set
        """
        self._check_executed()
        row = self._fetch_row()
        if row:
            return self._row_to_python(row, self.description)
        return None

    def fetchall(self):
        """Returns all rows of a query result set
        """
        if self._executed is None or self._rows is None:
            raise errors.InterfaceError(ERR_NO_RESULT_TO_FETCH)
        res = []
        for row in self._rows[self._next_row:]:
            res.append(self._row_to_python(
                row, self.description))
        self._next_row = len(self._rows)
        return res

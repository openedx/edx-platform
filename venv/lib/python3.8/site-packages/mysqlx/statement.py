# Copyright (c) 2016, 2020, Oracle and/or its affiliates.
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

"""Implementation of Statements."""

import copy
import json
import warnings

from .errors import ProgrammingError, NotSupportedError
from .expr import ExprParser
from .constants import LockContention
from .dbdoc import DbDoc
from .helpers import deprecated
from .result import Result
from .protobuf import mysqlxpb_enum

ERR_INVALID_INDEX_NAME = 'The given index name "{}" is not valid'


class Expr(object):
    """Expression wrapper."""
    def __init__(self, expr):
        self.expr = expr


def flexible_params(*values):
    """Parse flexible parameters."""
    if len(values) == 1 and isinstance(values[0], (list, tuple,)):
        return values[0]
    return values


def is_quoted_identifier(identifier, sql_mode=""):
    """Check if the given identifier is quoted.

    Args:
        identifier (string): Identifier to check.
        sql_mode (Optional[string]): SQL mode.

    Returns:
        `True` if the identifier has backtick quotes, and False otherwise.
    """
    if "ANSI_QUOTES" in sql_mode:
        return ((identifier[0] == "`" and identifier[-1] == "`") or
                (identifier[0] == '"' and identifier[-1] == '"'))
    return identifier[0] == "`" and identifier[-1] == "`"


def quote_identifier(identifier, sql_mode=""):
    """Quote the given identifier with backticks, converting backticks (`) in
    the identifier name with the correct escape sequence (``).

    Args:
        identifier (string): Identifier to quote.
        sql_mode (Optional[string]): SQL mode.

    Returns:
        A string with the identifier quoted with backticks.
    """
    if len(identifier) == 0:
        return "``"
    if "ANSI_QUOTES" in sql_mode:
        return '"{0}"'.format(identifier.replace('"', '""'))
    return "`{0}`".format(identifier.replace("`", "``"))


def quote_multipart_identifier(identifiers, sql_mode=""):
    """Quote the given multi-part identifier with backticks.

    Args:
        identifiers (iterable): List of identifiers to quote.
        sql_mode (Optional[string]): SQL mode.

    Returns:
        A string with the multi-part identifier quoted with backticks.
    """
    return ".".join([quote_identifier(identifier, sql_mode)
                     for identifier in identifiers])


def parse_table_name(default_schema, table_name, sql_mode=""):
    """Parse table name.

    Args:
        default_schema (str): The default schema.
        table_name (str): The table name.
        sql_mode(Optional[str]): The SQL mode.

    Returns:
        str: The parsed table name.
    """
    quote = '"' if "ANSI_QUOTES" in sql_mode else "`"
    delimiter = ".{0}".format(quote) if quote in table_name else "."
    temp = table_name.split(delimiter, 1)
    return (default_schema if len(temp) == 1 else temp[0].strip(quote),
            temp[-1].strip(quote),)


class Statement(object):
    """Provides base functionality for statement objects.

    Args:
        target (object): The target database object, it can be
                         :class:`mysqlx.Collection` or :class:`mysqlx.Table`.
        doc_based (bool): `True` if it is document based.
    """
    def __init__(self, target, doc_based=True):
        self._target = target
        self._doc_based = doc_based
        self._connection = target.get_connection() if target else None
        self._stmt_id = None
        self._exec_counter = 0
        self._changed = True
        self._prepared = False
        self._deallocate_prepare_execute = False

    @property
    def target(self):
        """object: The database object target."""
        return self._target

    @property
    def schema(self):
        """:class:`mysqlx.Schema`: The Schema object."""
        return self._target.schema

    @property
    def stmt_id(self):
        """Returns this statement ID.

        Returns:
            int: The statement ID.
        """
        return self._stmt_id

    @stmt_id.setter
    def stmt_id(self, value):
        self._stmt_id = value

    @property
    def exec_counter(self):
        """int: The number of times this statement was executed."""
        return self._exec_counter

    @property
    def changed(self):
        """bool: `True` if this statement has changes."""
        return self._changed

    @changed.setter
    def changed(self, value):
        self._changed = value

    @property
    def prepared(self):
        """bool: `True` if this statement has been prepared."""
        return self._prepared

    @prepared.setter
    def prepared(self, value):
        self._prepared = value

    @property
    def repeated(self):
        """bool: `True` if this statement was executed more than once.
        """
        return self._exec_counter > 1

    @property
    def deallocate_prepare_execute(self):
        """bool: `True` to deallocate + prepare + execute statement.
        """
        return self._deallocate_prepare_execute

    @deallocate_prepare_execute.setter
    def deallocate_prepare_execute(self, value):
        self._deallocate_prepare_execute = value

    def is_doc_based(self):
        """Check if it is document based.

        Returns:
            bool: `True` if it is document based.
        """
        return self._doc_based

    def increment_exec_counter(self):
        """Increments the number of times this statement has been executed."""
        self._exec_counter += 1

    def reset_exec_counter(self):
        """Resets the number of times this statement has been executed."""
        self._exec_counter = 0

    def execute(self):
        """Execute the statement.

        Raises:
           NotImplementedError: This method must be implemented.
        """
        raise NotImplementedError


class FilterableStatement(Statement):
    """A statement to be used with filterable statements.

    Args:
        target (object): The target database object, it can be
                         :class:`mysqlx.Collection` or :class:`mysqlx.Table`.
        doc_based (Optional[bool]): `True` if it is document based
                                    (default: `True`).
        condition (Optional[str]): Sets the search condition to filter
                                   documents or records.
    """
    def __init__(self, target, doc_based=True, condition=None):
        super(FilterableStatement, self).__init__(target=target,
                                                  doc_based=doc_based)
        self._binding_map = {}
        self._bindings = {}
        self._having = None
        self._grouping_str = ""
        self._grouping = None
        self._limit_offset = 0
        self._limit_row_count = None
        self._projection_str = ""
        self._projection_expr = None
        self._sort_str = ""
        self._sort_expr = None
        self._where_str = ""
        self._where_expr = None
        self.has_bindings = False
        self.has_limit = False
        self.has_group_by = False
        self.has_having = False
        self.has_projection = False
        self.has_sort = False
        self.has_where = False
        if condition:
            self._set_where(condition)

    def _bind_single(self, obj):
        """Bind single object.

        Args:
            obj (:class:`mysqlx.DbDoc` or str): DbDoc or JSON string object.

        Raises:
            :class:`mysqlx.ProgrammingError`: If invalid JSON string to bind.
            ValueError: If JSON loaded is not a dictionary.
        """
        if isinstance(obj, dict):
            self.bind(DbDoc(obj).as_str())
        elif isinstance(obj, DbDoc):
            self.bind(obj.as_str())
        elif isinstance(obj, str):
            try:
                res = json.loads(obj)
                if not isinstance(res, dict):
                    raise ValueError
            except ValueError:
                raise ProgrammingError("Invalid JSON string to bind")
            for key in res.keys():
                self.bind(key, res[key])
        else:
            raise ProgrammingError("Invalid JSON string or object to bind")

    def _sort(self, *clauses):
        """Sets the sorting criteria.

        Args:
            *clauses: The expression strings defining the sort criteria.

        Returns:
            mysqlx.FilterableStatement: FilterableStatement object.
        """
        self.has_sort = True
        self._sort_str = ",".join(flexible_params(*clauses))
        self._sort_expr = ExprParser(self._sort_str,
                                     not self._doc_based).parse_order_spec()
        self._changed = True
        return self

    def _set_where(self, condition):
        """Sets the search condition to filter.

        Args:
            condition (str): Sets the search condition to filter documents or
                             records.

        Returns:
            mysqlx.FilterableStatement: FilterableStatement object.
        """
        self.has_where = True
        self._where_str = condition
        try:
            expr = ExprParser(condition, not self._doc_based)
            self._where_expr = expr.expr()
        except ValueError:
            raise ProgrammingError("Invalid condition")
        self._binding_map = expr.placeholder_name_to_position
        self._changed = True
        return self

    def _set_group_by(self, *fields):
        """Set group by.

        Args:
            *fields: List of fields.
        """
        fields = flexible_params(*fields)
        self.has_group_by = True
        self._grouping_str = ",".join(fields)
        self._grouping = ExprParser(self._grouping_str,
                                    not self._doc_based).parse_expr_list()
        self._changed = True

    def _set_having(self, condition):
        """Set having.

        Args:
            condition (str): The condition.
        """
        self.has_having = True
        self._having = ExprParser(condition, not self._doc_based).expr()
        self._changed = True

    def _set_projection(self, *fields):
        """Set the projection.

        Args:
            *fields: List of fields.

        Returns:
            :class:`mysqlx.FilterableStatement`: Returns self.
        """
        fields = flexible_params(*fields)
        self.has_projection = True
        self._projection_str = ",".join(fields)
        self._projection_expr = ExprParser(
            self._projection_str,
            not self._doc_based).parse_table_select_projection()
        self._changed = True
        return self

    def get_binding_map(self):
        """Returns the binding map dictionary.

        Returns:
            dict: The binding map dictionary.
        """
        return self._binding_map

    def get_bindings(self):
        """Returns the bindings list.

        Returns:
            `list`: The bindings list.
        """
        return self._bindings

    def get_grouping(self):
        """Returns the grouping expression list.

        Returns:
            `list`: The grouping expression list.
        """
        return self._grouping

    def get_having(self):
        """Returns the having expression.

        Returns:
            object: The having expression.
        """
        return self._having

    def get_limit_row_count(self):
        """Returns the limit row count.

        Returns:
            int: The limit row count.
        """
        return self._limit_row_count

    def get_limit_offset(self):
        """Returns the limit offset.

        Returns:
            int: The limit offset.
        """
        return self._limit_offset

    def get_where_expr(self):
        """Returns the where expression.

        Returns:
            object: The where expression.
        """
        return self._where_expr

    def get_projection_expr(self):
        """Returns the projection expression.

        Returns:
            object: The projection expression.
        """
        return self._projection_expr

    def get_sort_expr(self):
        """Returns the sort expression.

        Returns:
            object: The sort expression.
        """
        return self._sort_expr

    @deprecated("8.0.12")
    def where(self, condition):
        """Sets the search condition to filter.

        Args:
            condition (str): Sets the search condition to filter documents or
                             records.

        Returns:
            mysqlx.FilterableStatement: FilterableStatement object.

        .. deprecated:: 8.0.12
        """
        return self._set_where(condition)

    @deprecated("8.0.12")
    def sort(self, *clauses):
        """Sets the sorting criteria.

        Args:
            *clauses: The expression strings defining the sort criteria.

        Returns:
            mysqlx.FilterableStatement: FilterableStatement object.

        .. deprecated:: 8.0.12
        """
        return self._sort(*clauses)

    def limit(self, row_count, offset=None):
        """Sets the maximum number of items to be returned.

        Args:
            row_count (int): The maximum number of items.

        Returns:
            mysqlx.FilterableStatement: FilterableStatement object.

        Raises:
            ValueError: If ``row_count`` is not a positive integer.

        .. versionchanged:: 8.0.12
           The usage of ``offset`` was deprecated.
        """
        if not isinstance(row_count, int) or row_count < 0:
            raise ValueError("The 'row_count' value must be a positive integer")
        if not self.has_limit:
            self._changed = bool(self._exec_counter == 0)
            self._deallocate_prepare_execute = bool(not self._exec_counter == 0)

        self._limit_row_count = row_count
        self.has_limit = True
        if offset:
            self.offset(offset)
            warnings.warn("'limit(row_count, offset)' is deprecated, please "
                          "use 'offset(offset)' to set the number of items to "
                          "skip", category=DeprecationWarning)
        return self

    def offset(self, offset):
        """Sets the number of items to skip.

        Args:
            offset (int): The number of items to skip.

        Returns:
            mysqlx.FilterableStatement: FilterableStatement object.

        Raises:
            ValueError: If ``offset`` is not a positive integer.

        .. versionadded:: 8.0.12
        """
        if not isinstance(offset, int) or offset < 0:
            raise ValueError("The 'offset' value must be a positive integer")
        self._limit_offset = offset
        return self

    def bind(self, *args):
        """Binds value(s) to a specific placeholder(s).

        Args:
            *args: The name of the placeholder and the value to bind.
                   A :class:`mysqlx.DbDoc` object or a JSON string
                   representation can be used.

        Returns:
            mysqlx.FilterableStatement: FilterableStatement object.

        Raises:
            ProgrammingError: If the number of arguments is invalid.
        """
        self.has_bindings = True
        count = len(args)
        if count == 1:
            self._bind_single(args[0])
        elif count == 2:
            self._bindings[args[0]] = args[1]
        else:
            raise ProgrammingError("Invalid number of arguments to bind")
        return self

    def execute(self):
        """Execute the statement.

        Raises:
           NotImplementedError: This method must be implemented.
        """
        raise NotImplementedError


class SqlStatement(Statement):
    """A statement for SQL execution.

    Args:
        connection (mysqlx.connection.Connection): Connection object.
        sql (string): The sql statement to be executed.
    """
    def __init__(self, connection, sql):
        super(SqlStatement, self).__init__(target=None, doc_based=False)
        self._connection = connection
        self._sql = sql
        self._binding_map = None
        self._bindings = []
        self.has_bindings = False
        self.has_limit = False

    @property
    def sql(self):
        """string: The SQL text statement."""
        return self._sql

    def get_binding_map(self):
        """Returns the binding map dictionary.

        Returns:
            dict: The binding map dictionary.
        """
        return self._binding_map

    def get_bindings(self):
        """Returns the bindings list.

        Returns:
            `list`: The bindings list.
        """
        return self._bindings

    def bind(self, *args):
        """Binds value(s) to a specific placeholder(s).

        Args:
            *args: The value(s) to bind.

        Returns:
            mysqlx.SqlStatement: SqlStatement object.
        """
        if len(args) == 0:
            raise ProgrammingError("Invalid number of arguments to bind")
        self.has_bindings = True
        bindings = flexible_params(*args)
        if isinstance(bindings, (list, tuple)):
            self._bindings = bindings
        else:
            self._bindings.append(bindings)
        return self

    def execute(self):
        """Execute the statement.

        Returns:
            mysqlx.SqlResult: SqlResult object.
        """
        return self._connection.send_sql(self)


class WriteStatement(Statement):
    """Provide common write operation attributes.
    """
    def __init__(self, target, doc_based):
        super(WriteStatement, self).__init__(target, doc_based)
        self._values = []

    def get_values(self):
        """Returns the list of values.

        Returns:
            `list`: The list of values.
        """
        return self._values

    def execute(self):
        """Execute the statement.

        Raises:
           NotImplementedError: This method must be implemented.
        """
        raise NotImplementedError


class AddStatement(WriteStatement):
    """A statement for document addition on a collection.

    Args:
        collection (mysqlx.Collection): The Collection object.
    """
    def __init__(self, collection):
        super(AddStatement, self).__init__(collection, True)
        self._upsert = False
        self.ids = []

    def is_upsert(self):
        """Returns `True` if it's an upsert.

        Returns:
            bool: `True` if it's an upsert.
        """
        return self._upsert

    def upsert(self, value=True):
        """Sets the upset flag to the boolean of the value provided.
        Setting of this flag allows updating of the matched rows/documents
        with the provided value.

        Args:
            value (optional[bool]): Set or unset the upsert flag.
        """
        self._upsert = value
        return self

    def add(self, *values):
        """Adds a list of documents into a collection.

        Args:
            *values: The documents to be added into the collection.

        Returns:
            mysqlx.AddStatement: AddStatement object.
        """
        for val in flexible_params(*values):
            if isinstance(val, DbDoc):
                self._values.append(val)
            else:
                self._values.append(DbDoc(val))
        return self

    def execute(self):
        """Execute the statement.

        Returns:
            mysqlx.Result: Result object.
        """
        if len(self._values) == 0:
            return Result()

        return self._connection.send_insert(self)


class UpdateSpec(object):
    """Update specification class implementation.

    Args:
        update_type (int): The update type.
        source (str): The source.
        value (Optional[str]): The value.
    """
    def __init__(self, update_type, source, value=None):
        if update_type == mysqlxpb_enum(
                "Mysqlx.Crud.UpdateOperation.UpdateType.SET"):
            self._table_set(source, value)
        else:
            self.update_type = update_type
            self.source = source
            if len(source) > 0 and source[0] == '$':
                self.source = source[1:]
            self.source = ExprParser(self.source,
                                     False).document_field().identifier
            self.value = value

    def _table_set(self, source, value):
        """Table set.

        Args:
            source (str): The source.
            value (str): The value.
        """
        self.update_type = mysqlxpb_enum(
            "Mysqlx.Crud.UpdateOperation.UpdateType.SET")
        self.source = ExprParser(source, True).parse_table_update_field()
        self.value = value


class ModifyStatement(FilterableStatement):
    """A statement for document update operations on a Collection.

    Args:
        collection (mysqlx.Collection): The Collection object.
        condition (str): Sets the search condition to identify the documents
                         to be modified.

    .. versionchanged:: 8.0.12
       The ``condition`` parameter is now mandatory.
    """
    def __init__(self, collection, condition):
        super(ModifyStatement, self).__init__(target=collection,
                                              condition=condition)
        self._update_ops = {}

    def sort(self, *clauses):
        """Sets the sorting criteria.

        Args:
            *clauses: The expression strings defining the sort criteria.

        Returns:
            mysqlx.ModifyStatement: ModifyStatement object.
        """
        return self._sort(*clauses)

    def get_update_ops(self):
        """Returns the list of update operations.

        Returns:
            `list`: The list of update operations.
        """
        return self._update_ops

    def set(self, doc_path, value):
        """Sets or updates attributes on documents in a collection.

        Args:
            doc_path (string): The document path of the item to be set.
            value (string): The value to be set on the specified attribute.

        Returns:
            mysqlx.ModifyStatement: ModifyStatement object.
        """
        self._update_ops[doc_path] = UpdateSpec(mysqlxpb_enum(
            "Mysqlx.Crud.UpdateOperation.UpdateType.ITEM_SET"),
                                                doc_path, value)
        self._changed = True
        return self

    @deprecated("8.0.12")
    def change(self, doc_path, value):
        """Add an update to the statement setting the field, if it exists at
        the document path, to the given value.

        Args:
            doc_path (string): The document path of the item to be set.
            value (object): The value to be set on the specified attribute.

        Returns:
            mysqlx.ModifyStatement: ModifyStatement object.

        .. deprecated:: 8.0.12
        """
        self._update_ops[doc_path] = UpdateSpec(mysqlxpb_enum(
            "Mysqlx.Crud.UpdateOperation.UpdateType.ITEM_REPLACE"),
                                                doc_path, value)
        self._changed = True
        return self

    def unset(self, *doc_paths):
        """Removes attributes from documents in a collection.

        Args:
            doc_paths (list): The list of document paths of the attributes to be
                              removed.

        Returns:
            mysqlx.ModifyStatement: ModifyStatement object.
        """
        for item in flexible_params(*doc_paths):
            self._update_ops[item] = UpdateSpec(mysqlxpb_enum(
                "Mysqlx.Crud.UpdateOperation.UpdateType.ITEM_REMOVE"), item)
        self._changed = True
        return self

    def array_insert(self, field, value):
        """Insert a value into the specified array in documents of a
        collection.

        Args:
            field (string): A document path that identifies the array attribute
                            and position where the value will be inserted.
            value (object): The value to be inserted.

        Returns:
            mysqlx.ModifyStatement: ModifyStatement object.
        """
        self._update_ops[field] = UpdateSpec(mysqlxpb_enum(
            "Mysqlx.Crud.UpdateOperation.UpdateType.ARRAY_INSERT"),
                                             field, value)
        self._changed = True
        return self

    def array_append(self, doc_path, value):
        """Inserts a value into a specific position in an array attribute in
        documents of a collection.

        Args:
            doc_path (string): A document path that identifies the array
                               attribute and position where the value will be
                               inserted.
            value (object): The value to be inserted.

        Returns:
            mysqlx.ModifyStatement: ModifyStatement object.
        """
        self._update_ops[doc_path] = UpdateSpec(mysqlxpb_enum(
            "Mysqlx.Crud.UpdateOperation.UpdateType.ARRAY_APPEND"),
                                                doc_path, value)
        self._changed = True
        return self

    def patch(self, doc):
        """Takes a :class:`mysqlx.DbDoc`, string JSON format or a dict with the
        changes and applies it on all matching documents.

        Args:
            doc (object): A generic document (DbDoc), string in JSON format or
                          dict, with the changes to apply to the matching
                          documents.

        Returns:
            mysqlx.ModifyStatement: ModifyStatement object.
        """
        if doc is None:
            doc = ''
        if not isinstance(doc, (ExprParser, dict, DbDoc, str)):
            raise ProgrammingError(
                "Invalid data for update operation on document collection "
                "table")
        self._update_ops["patch"] = UpdateSpec(
            mysqlxpb_enum("Mysqlx.Crud.UpdateOperation.UpdateType.MERGE_PATCH"),
            '', doc.expr() if isinstance(doc, ExprParser) else doc)
        self._changed = True
        return self

    def execute(self):
        """Execute the statement.

        Returns:
            mysqlx.Result: Result object.

        Raises:
            ProgrammingError: If condition was not set.
        """
        if not self.has_where:
            raise ProgrammingError("No condition was found for modify")
        return self._connection.send_update(self)


class ReadStatement(FilterableStatement):
    """Provide base functionality for Read operations

    Args:
        target (object): The target database object, it can be
                         :class:`mysqlx.Collection` or :class:`mysqlx.Table`.
        doc_based (Optional[bool]): `True` if it is document based
                                    (default: `True`).
        condition (Optional[str]): Sets the search condition to filter
                                   documents or records.
    """
    def __init__(self, target, doc_based=True, condition=None):
        super(ReadStatement, self).__init__(target, doc_based, condition)
        self._lock_exclusive = False
        self._lock_shared = False
        self._lock_contention = LockContention.DEFAULT

    @property
    def lock_contention(self):
        """:class:`mysqlx.LockContention`: The lock contention value."""
        return self._lock_contention

    def _set_lock_contention(self, lock_contention):
        """Set the lock contention.

        Args:
            lock_contention (:class:`mysqlx.LockContention`): Lock contention.

        Raises:
            ProgrammingError: If is an invalid lock contention value.
        """
        try:
            # Check if is a valid lock contention value
            _ = LockContention.index(lock_contention)
        except ValueError:
            raise ProgrammingError("Invalid lock contention mode. Use 'NOWAIT' "
                                   "or 'SKIP_LOCKED'")
        self._lock_contention = lock_contention

    def is_lock_exclusive(self):
        """Returns `True` if is `EXCLUSIVE LOCK`.

        Returns:
            bool: `True` if is `EXCLUSIVE LOCK`.
        """
        return self._lock_exclusive

    def is_lock_shared(self):
        """Returns `True` if is `SHARED LOCK`.

        Returns:
            bool: `True` if is `SHARED LOCK`.
        """
        return self._lock_shared

    def lock_shared(self, lock_contention=LockContention.DEFAULT):
        """Execute a read operation with `SHARED LOCK`. Only one lock can be
           active at a time.

        Args:
            lock_contention (:class:`mysqlx.LockContention`): Lock contention.
        """
        self._lock_exclusive = False
        self._lock_shared = True
        self._set_lock_contention(lock_contention)
        return self

    def lock_exclusive(self, lock_contention=LockContention.DEFAULT):
        """Execute a read operation with `EXCLUSIVE LOCK`. Only one lock can be
           active at a time.

        Args:
            lock_contention (:class:`mysqlx.LockContention`): Lock contention.
        """
        self._lock_exclusive = True
        self._lock_shared = False
        self._set_lock_contention(lock_contention)
        return self

    def group_by(self, *fields):
        """Sets a grouping criteria for the resultset.

        Args:
            *fields: The string expressions identifying the grouping criteria.

        Returns:
            mysqlx.ReadStatement: ReadStatement object.
        """
        self._set_group_by(*fields)
        return self

    def having(self, condition):
        """Sets a condition for records to be considered in agregate function
        operations.

        Args:
            condition (string): A condition on the agregate functions used on
                                the grouping criteria.

        Returns:
            mysqlx.ReadStatement: ReadStatement object.
        """
        self._set_having(condition)
        return self

    def execute(self):
        """Execute the statement.

        Returns:
            mysqlx.Result: Result object.
        """
        return self._connection.send_find(self)


class FindStatement(ReadStatement):
    """A statement document selection on a Collection.

    Args:
        collection (mysqlx.Collection): The Collection object.
        condition (Optional[str]): An optional expression to identify the
                                   documents to be retrieved. If not specified
                                   all the documents will be included on the
                                   result unless a limit is set.
    """
    def __init__(self, collection, condition=None):
        super(FindStatement, self).__init__(collection, True, condition)

    def fields(self, *fields):
        """Sets a document field filter.

        Args:
            *fields: The string expressions identifying the fields to be
                     extracted.

        Returns:
            mysqlx.FindStatement: FindStatement object.
        """
        return self._set_projection(*fields)

    def sort(self, *clauses):
        """Sets the sorting criteria.

        Args:
            *clauses: The expression strings defining the sort criteria.

        Returns:
            mysqlx.FindStatement: FindStatement object.
        """
        return self._sort(*clauses)


class SelectStatement(ReadStatement):
    """A statement for record retrieval operations on a Table.

    Args:
        table (mysqlx.Table): The Table object.
        *fields: The fields to be retrieved.
    """
    def __init__(self, table, *fields):
        super(SelectStatement, self).__init__(table, False)
        self._set_projection(*fields)

    def where(self, condition):
        """Sets the search condition to filter.

        Args:
            condition (str): Sets the search condition to filter records.

        Returns:
            mysqlx.SelectStatement: SelectStatement object.
        """
        return self._set_where(condition)

    def order_by(self, *clauses):
        """Sets the order by criteria.

        Args:
            *clauses: The expression strings defining the order by criteria.

        Returns:
            mysqlx.SelectStatement: SelectStatement object.
        """
        return self._sort(*clauses)

    def get_sql(self):
        """Returns the generated SQL.

        Returns:
            str: The generated SQL.
        """
        where = " WHERE {0}".format(self._where_str) if self.has_where else ""
        group_by = " GROUP BY {0}".format(self._grouping_str) if \
            self.has_group_by else ""
        having = " HAVING {0}".format(self._having) if self.has_having else ""
        order_by = " ORDER BY {0}".format(self._sort_str) if self.has_sort \
            else ""
        limit = " LIMIT {0} OFFSET {1}".format(self._limit_row_count,
                                               self._limit_offset) \
                                               if self.has_limit else ""
        stmt = ("SELECT {select} FROM {schema}.{table}{where}{group}{having}"
                "{order}{limit}".format(select=self._projection_str or "*",
                                        schema=self.schema.name,
                                        table=self.target.name, limit=limit,
                                        where=where, group=group_by,
                                        having=having, order=order_by))
        return stmt


class InsertStatement(WriteStatement):
    """A statement for insert operations on Table.

    Args:
        table (mysqlx.Table): The Table object.
        *fields: The fields to be inserted.
    """
    def __init__(self, table, *fields):
        super(InsertStatement, self).__init__(table, False)
        self._fields = flexible_params(*fields)

    def values(self, *values):
        """Set the values to be inserted.

        Args:
            *values: The values of the columns to be inserted.

        Returns:
            mysqlx.InsertStatement: InsertStatement object.
        """
        self._values.append(list(flexible_params(*values)))
        return self

    def execute(self):
        """Execute the statement.

        Returns:
            mysqlx.Result: Result object.
        """
        return self._connection.send_insert(self)


class UpdateStatement(FilterableStatement):
    """A statement for record update operations on a Table.

    Args:
        table (mysqlx.Table): The Table object.

    .. versionchanged:: 8.0.12
       The ``fields`` parameters were removed.
    """
    def __init__(self, table):
        super(UpdateStatement, self).__init__(target=table, doc_based=False)
        self._update_ops = {}

    def where(self, condition):
        """Sets the search condition to filter.

        Args:
            condition (str): Sets the search condition to filter records.

        Returns:
            mysqlx.UpdateStatement: UpdateStatement object.
        """
        return self._set_where(condition)

    def order_by(self, *clauses):
        """Sets the order by criteria.

        Args:
            *clauses: The expression strings defining the order by criteria.

        Returns:
            mysqlx.UpdateStatement: UpdateStatement object.
        """
        return self._sort(*clauses)

    def get_update_ops(self):
        """Returns the list of update operations.

        Returns:
            `list`: The list of update operations.
        """
        return self._update_ops

    def set(self, field, value):
        """Updates the column value on records in a table.

        Args:
            field (string): The column name to be updated.
            value (object): The value to be set on the specified column.

        Returns:
            mysqlx.UpdateStatement: UpdateStatement object.
        """
        self._update_ops[field] = UpdateSpec(mysqlxpb_enum(
            "Mysqlx.Crud.UpdateOperation.UpdateType.SET"), field, value)
        self._changed = True
        return self

    def execute(self):
        """Execute the statement.

        Returns:
            mysqlx.Result: Result object

        Raises:
            ProgrammingError: If condition was not set.
        """
        if not self.has_where:
            raise ProgrammingError("No condition was found for update")
        return self._connection.send_update(self)


class RemoveStatement(FilterableStatement):
    """A statement for document removal from a collection.

    Args:
        collection (mysqlx.Collection): The Collection object.
        condition (str): Sets the search condition to identify the documents
                         to be removed.

    .. versionchanged:: 8.0.12
       The ``condition`` parameter was added.
    """
    def __init__(self, collection, condition):
        super(RemoveStatement, self).__init__(target=collection,
                                              condition=condition)

    def sort(self, *clauses):
        """Sets the sorting criteria.

        Args:
            *clauses: The expression strings defining the sort criteria.

        Returns:
            mysqlx.FindStatement: FindStatement object.
        """
        return self._sort(*clauses)

    def execute(self):
        """Execute the statement.

        Returns:
            mysqlx.Result: Result object.

        Raises:
            ProgrammingError: If condition was not set.
        """
        if not self.has_where:
            raise ProgrammingError("No condition was found for remove")
        return self._connection.send_delete(self)


class DeleteStatement(FilterableStatement):
    """A statement that drops a table.

    Args:
        table (mysqlx.Table): The Table object.

    .. versionchanged:: 8.0.12
       The ``condition`` parameter was removed.
    """
    def __init__(self, table):
        super(DeleteStatement, self).__init__(target=table, doc_based=False)

    def where(self, condition):
        """Sets the search condition to filter.

        Args:
            condition (str): Sets the search condition to filter records.

        Returns:
            mysqlx.DeleteStatement: DeleteStatement object.
        """
        return self._set_where(condition)

    def order_by(self, *clauses):
        """Sets the order by criteria.

        Args:
            *clauses: The expression strings defining the order by criteria.

        Returns:
            mysqlx.DeleteStatement: DeleteStatement object.
        """
        return self._sort(*clauses)

    def execute(self):
        """Execute the statement.

        Returns:
            mysqlx.Result: Result object.

        Raises:
            ProgrammingError: If condition was not set.
        """
        if not self.has_where:
            raise ProgrammingError("No condition was found for delete")
        return self._connection.send_delete(self)


class CreateCollectionIndexStatement(Statement):
    """A statement that creates an index on a collection.

    Args:
        collection (mysqlx.Collection): Collection.
        index_name (string): Index name.
        index_desc (dict): A dictionary containing the fields members that
                           constraints the index to be created. It must have
                           the form as shown in the following::

                               {"fields": [{"field": member_path,
                                            "type": member_type,
                                            "required": member_required,
                                            "collation": collation,
                                            "options": options,
                                            "srid": srid},
                                            # {... more members,
                                            #      repeated as many times
                                            #      as needed}
                                            ],
                                "type": type}
    """
    def __init__(self, collection, index_name, index_desc):
        super(CreateCollectionIndexStatement, self).__init__(target=collection)
        self._index_desc = copy.deepcopy(index_desc)
        self._index_name = index_name
        self._fields_desc = self._index_desc.pop("fields", [])

    def execute(self):
        """Execute the statement.

        Returns:
            mysqlx.Result: Result object.
        """
        # Validate index name is a valid identifier
        if self._index_name is None:
            raise ProgrammingError(
                ERR_INVALID_INDEX_NAME.format(self._index_name))
        try:
            parsed_ident = ExprParser(self._index_name).expr().get_message()

            # The message is type dict when the Protobuf cext is used
            if isinstance(parsed_ident, dict):
                if parsed_ident["type"] != mysqlxpb_enum(
                        "Mysqlx.Expr.Expr.Type.IDENT"):
                    raise ProgrammingError(
                        ERR_INVALID_INDEX_NAME.format(self._index_name))
            else:
                if parsed_ident.type != mysqlxpb_enum(
                        "Mysqlx.Expr.Expr.Type.IDENT"):
                    raise ProgrammingError(
                        ERR_INVALID_INDEX_NAME.format(self._index_name))

        except (ValueError, AttributeError):
            raise ProgrammingError(
                ERR_INVALID_INDEX_NAME.format(self._index_name))

        # Validate members that constraint the index
        if not self._fields_desc:
            raise ProgrammingError("Required member 'fields' not found in "
                                   "the given index description: {}"
                                   "".format(self._index_desc))

        if not isinstance(self._fields_desc, list):
            raise ProgrammingError("Required member 'fields' must contain a "
                                   "list.")

        args = {}
        args["name"] = self._index_name
        args["collection"] = self._target.name
        args["schema"] = self._target.schema.name
        if "type" in self._index_desc:
            args["type"] = self._index_desc.pop("type")
        else:
            args["type"] = "INDEX"
        args["unique"] = self._index_desc.pop("unique", False)
        # Currently unique indexes are not supported:
        if args["unique"]:
            raise NotSupportedError("Unique indexes are not supported.")
        args["constraint"] = []

        if self._index_desc:
            raise ProgrammingError("Unidentified fields: {}"
                                   "".format(self._index_desc))

        try:
            for field_desc in self._fields_desc:
                constraint = {}
                constraint["member"] = field_desc.pop("field")
                constraint["type"] = field_desc.pop("type")
                constraint["required"] = field_desc.pop("required", False)
                constraint["array"] = field_desc.pop("array", False)
                if not isinstance(constraint["required"], bool):
                    raise TypeError("Field member 'required' must be Boolean")
                if not isinstance(constraint["array"], bool):
                    raise TypeError("Field member 'array' must be Boolean")
                if args["type"].upper() == "SPATIAL" and \
                   not constraint["required"]:
                    raise ProgrammingError(
                        "Field member 'required' must be set to 'True' when "
                        "index type is set to 'SPATIAL'")
                if args["type"].upper() == "INDEX" and \
                   constraint["type"] == "GEOJSON":
                    raise ProgrammingError(
                        "Index 'type' must be set to 'SPATIAL' when field "
                        "type is set to 'GEOJSON'")
                if "collation" in field_desc:
                    if not constraint["type"].upper().startswith("TEXT"):
                        raise ProgrammingError(
                            "The 'collation' member can only be used when "
                            "field type is set to '{}'"
                            "".format(constraint["type"].upper()))
                    constraint["collation"] = field_desc.pop("collation")
                # "options" and "srid" fields in IndexField can be
                # present only if "type" is set to "GEOJSON"
                if "options" in field_desc:
                    if constraint["type"].upper() != "GEOJSON":
                        raise ProgrammingError(
                            "The 'options' member can only be used when "
                            "index type is set to 'GEOJSON'")
                    constraint["options"] = field_desc.pop("options")
                if "srid" in field_desc:
                    if constraint["type"].upper() != "GEOJSON":
                        raise ProgrammingError(
                            "The 'srid' member can only be used when index "
                            "type is set to 'GEOJSON'")
                    constraint["srid"] = field_desc.pop("srid")
                args["constraint"].append(constraint)
        except KeyError as err:
            raise ProgrammingError("Required inner member {} not found in "
                                   "constraint: {}".format(err, field_desc))

        for field_desc in self._fields_desc:
            if field_desc:
                raise ProgrammingError("Unidentified inner fields:{}"
                                       "".format(field_desc))

        return self._connection.execute_nonquery(
            "mysqlx", "create_collection_index", True, args)

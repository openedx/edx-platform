# Copyright (c) 2016, 2021, Oracle and/or its affiliates.
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

"""Implementation of the CRUD database objects."""

import json
import warnings

from .dbdoc import DbDoc
from .errorcode import (ER_NO_SUCH_TABLE, ER_TABLE_EXISTS_ERROR,
                        ER_X_CMD_NUM_ARGUMENTS, ER_X_INVALID_ADMIN_COMMAND)
from .errors import NotSupportedError, OperationalError, ProgrammingError
from .helpers import deprecated, escape, quote_identifier
from .statement import (FindStatement, AddStatement, RemoveStatement,
                        ModifyStatement, SelectStatement, InsertStatement,
                        DeleteStatement, UpdateStatement,
                        CreateCollectionIndexStatement)


_COUNT_VIEWS_QUERY = ("SELECT COUNT(*) FROM information_schema.views "
                      "WHERE table_schema = '{0}' AND table_name = '{1}'")
_COUNT_TABLES_QUERY = ("SELECT COUNT(*) FROM information_schema.tables "
                       "WHERE table_schema = '{0}' AND table_name = '{1}'")
_COUNT_SCHEMAS_QUERY = ("SELECT COUNT(*) FROM information_schema.schemata "
                        "WHERE schema_name = '{0}'")
_COUNT_QUERY = "SELECT COUNT(*) FROM {0}.{1}"
_DROP_TABLE_QUERY = "DROP TABLE IF EXISTS {0}.{1}"


class DatabaseObject(object):
    """Provides base functionality for database objects.

    Args:
        schema (mysqlx.Schema): The Schema object.
        name (str): The database object name.
    """
    def __init__(self, schema, name):
        self._schema = schema
        self._name = name.decode() if isinstance(name, bytes) else name
        self._session = self._schema.get_session()
        self._connection = self._session.get_connection()

    @property
    def session(self):
        """:class:`mysqlx.Session`: The Session object.
        """
        return self._session

    @property
    def schema(self):
        """:class:`mysqlx.Schema`: The Schema object.
        """
        return self._schema

    @property
    def name(self):
        """str: The name of this database object.
        """
        return self._name

    def get_connection(self):
        """Returns the underlying connection.

        Returns:
            mysqlx.connection.Connection: The connection object.
        """
        return self._connection

    def get_session(self):
        """Returns the session of this database object.

        Returns:
            mysqlx.Session: The Session object.
        """
        return self._session

    def get_schema(self):
        """Returns the Schema object of this database object.

        Returns:
            mysqlx.Schema: The Schema object.
        """
        return self._schema

    def get_name(self):
        """Returns the name of this database object.

        Returns:
            str: The name of this database object.
        """
        return self._name

    def exists_in_database(self):
        """Verifies if this object exists in the database.

        Returns:
            bool: `True` if object exists in database.

        Raises:
           NotImplementedError: This method must be implemented.
        """
        raise NotImplementedError

    @deprecated("8.0.12", "Use 'exists_in_database()' method instead")
    def am_i_real(self):
        """Verifies if this object exists in the database.

        Returns:
            bool: `True` if object exists in database.

        Raises:
           NotImplementedError: This method must be implemented.

        .. deprecated:: 8.0.12
           Use ``exists_in_database()`` method instead.
        """
        return self.exists_in_database()

    @deprecated("8.0.12", "Use 'get_name()' method instead")
    def who_am_i(self):
        """Returns the name of this database object.

        Returns:
            str: The name of this database object.

        .. deprecated:: 8.0.12
           Use ``get_name()`` method instead.
        """
        return self.get_name()


class Schema(DatabaseObject):
    """A client-side representation of a database schema. Provides access to
    the schema contents.

    Args:
        session (mysqlx.XSession): Session object.
        name (str): The Schema name.
    """
    def __init__(self, session, name):
        self._session = session
        super(Schema, self).__init__(self, name)

    def exists_in_database(self):
        """Verifies if this object exists in the database.

        Returns:
            bool: `True` if object exists in database.
        """
        sql = _COUNT_SCHEMAS_QUERY.format(escape(self._name))
        return self._connection.execute_sql_scalar(sql) == 1

    def get_collections(self):
        """Returns a list of collections for this schema.

        Returns:
            `list`: List of Collection objects.
        """
        rows = self._connection.get_row_result("list_objects",
                                               {"schema": self._name})
        rows.fetch_all()
        collections = []
        for row in rows:
            if row["type"] != "COLLECTION":
                continue
            try:
                collection = Collection(self, row["TABLE_NAME"])
            except ValueError:
                collection = Collection(self, row["name"])
            collections.append(collection)
        return collections

    def get_collection_as_table(self, name, check_existence=False):
        """Returns a a table object for the given collection

        Returns:
            mysqlx.Table: Table object.

        """
        return self.get_table(name, check_existence)

    def get_tables(self):
        """Returns a list of tables for this schema.

        Returns:
            `list`: List of Table objects.
        """
        rows = self._connection.get_row_result("list_objects",
                                               {"schema": self._name})
        rows.fetch_all()
        tables = []
        object_types = ("TABLE", "VIEW",)
        for row in rows:
            if row["type"] in object_types:
                try:
                    table = Table(self, row["TABLE_NAME"])
                except ValueError:
                    table = Table(self, row["name"])
                tables.append(table)
        return tables

    def get_table(self, name, check_existence=False):
        """Returns the table of the given name for this schema.

        Returns:
            mysqlx.Table: Table object.
        """
        table = Table(self, name)
        if check_existence:
            if not table.exists_in_database():
                raise ProgrammingError("Table does not exist")
        return table

    def get_view(self, name, check_existence=False):
        """Returns the view of the given name for this schema.

        Returns:
            mysqlx.View: View object.
        """
        view = View(self, name)
        if check_existence:
            if not view.exists_in_database():
                raise ProgrammingError("View does not exist")
        return view

    def get_collection(self, name, check_existence=False):
        """Returns the collection of the given name for this schema.

        Returns:
            mysqlx.Collection: Collection object.
        """
        collection = Collection(self, name)
        if check_existence:
            if not collection.exists_in_database():
                raise ProgrammingError("Collection does not exist")
        return collection

    def drop_collection(self, name):
        """Drops a collection.

        Args:
            name (str): The name of the collection to be dropped.
        """
        self._connection.execute_nonquery(
            "sql", _DROP_TABLE_QUERY.format(quote_identifier(self._name),
                                            quote_identifier(name)), False)

    def create_collection(self, name, reuse_existing=False, validation=None,
                          **kwargs):
        """Creates in the current schema a new collection with the specified
        name and retrieves an object representing the new collection created.

        Args:
            name (str): The name of the collection.
            reuse_existing (bool): `True` to reuse an existing collection.
            validation (Optional[dict]): A dict, containing the keys `level`
                                         with the validation level and `schema`
                                         with a dict or a string representation
                                         of a JSON schema specification.

        Returns:
            mysqlx.Collection: Collection object.

        Raises:
            :class:`mysqlx.ProgrammingError`: If ``reuse_existing`` is False
                                              and collection exists or the
                                              collection name is invalid.
            :class:`mysqlx.NotSupportedError`: If schema validation is not
                                               supported by the server.

        .. versionchanged:: 8.0.21
        """
        if not name:
            raise ProgrammingError("Collection name is invalid")

        if "reuse" in kwargs:
            warnings.warn("'reuse' is deprecated since 8.0.21. "
                          "Please use 'reuse_existing' instead",
                          DeprecationWarning)
            reuse_existing = kwargs["reuse"]

        collection = Collection(self, name)
        fields = {"schema": self._name, "name": name}

        if validation is not None:
            if not isinstance(validation, dict) or not validation:
                raise ProgrammingError("Invalid value for 'validation'")

            valid_options = ("level", "schema")
            for option in validation:
                if option not in valid_options:
                    raise ProgrammingError("Invalid option in 'validation': {}"
                                           "".format(option))

            options = []

            if "level" in validation:
                level = validation["level"]
                if not isinstance(level, str):
                    raise ProgrammingError("Invalid value for 'level'")
                options.append(("level", level))

            if "schema" in validation:
                schema = validation["schema"]
                if not isinstance(schema, (str, dict)):
                    raise ProgrammingError("Invalid value for 'schema'")
                options.append(
                    ("schema", json.dumps(schema)
                               if isinstance(schema, dict) else schema))

            fields["options"] = ("validation", options)

        try:
            self._connection.execute_nonquery(
                "mysqlx", "create_collection", True, fields)
        except OperationalError as err:
            if err.errno == ER_X_CMD_NUM_ARGUMENTS:
                raise NotSupportedError(
                    "Your MySQL server does not support the requested "
                    "operation. Please update to MySQL 8.0.19 or a later "
                    "version")
            if err.errno == ER_TABLE_EXISTS_ERROR:
                if not reuse_existing:
                    raise ProgrammingError(
                        "Collection '{}' already exists".format(name))
            else:
                raise ProgrammingError(err.msg, err.errno)

        return collection

    def modify_collection(self, name, validation=None):
        """Modifies a collection using a JSON schema validation.

        Args:
            name (str): The name of the collection.
            validation (Optional[dict]): A dict, containing the keys `level`
                                         with the validation level and `schema`
                                         with a dict or a string representation
                                         of a JSON schema specification.

        Raises:
            :class:`mysqlx.ProgrammingError`: If the collection name or
                                              validation is invalid.
            :class:`mysqlx.NotSupportedError`: If schema validation is not
                                               supported by the server.

        .. versionadded:: 8.0.21
        """
        if not name:
            raise ProgrammingError("Collection name is invalid")

        if not isinstance(validation, dict) or not validation:
            raise ProgrammingError("Invalid value for 'validation'")

        valid_options = ("level", "schema")
        for option in validation:
            if option not in valid_options:
                raise ProgrammingError("Invalid option in 'validation': {}"
                                       "".format(option))
        options = []

        if "level" in validation:
            level = validation["level"]
            if not isinstance(level, str):
                raise ProgrammingError("Invalid value for 'level'")
            options.append(("level", level))

        if "schema" in validation:
            schema = validation["schema"]
            if not isinstance(schema, (str, dict)):
                raise ProgrammingError("Invalid value for 'schema'")
            options.append(
                ("schema", json.dumps(schema)
                           if isinstance(schema, dict) else schema))

        fields = {
            "schema": self._name,
            "name": name,
            "options": ("validation", options)
        }

        try:
            self._connection.execute_nonquery(
                "mysqlx", "modify_collection_options", True, fields)
        except OperationalError as err:
            if err.errno == ER_X_INVALID_ADMIN_COMMAND:
                raise NotSupportedError(
                    "Your MySQL server does not support the requested "
                    "operation. Please update to MySQL 8.0.19 or a later "
                    "version")
            raise ProgrammingError(err.msg, err.errno)


class Collection(DatabaseObject):
    """Represents a collection of documents on a schema.

    Args:
        schema (mysqlx.Schema): The Schema object.
        name (str): The collection name.
    """

    def exists_in_database(self):
        """Verifies if this object exists in the database.

        Returns:
            bool: `True` if object exists in database.
        """
        sql = _COUNT_TABLES_QUERY.format(escape(self._schema.name),
                                         escape(self._name))
        return self._connection.execute_sql_scalar(sql) == 1

    def find(self, condition=None):
        """Retrieves documents from a collection.

        Args:
            condition (Optional[str]): The string with the filter expression of
                                       the documents to be retrieved.
        """
        stmt = FindStatement(self, condition)
        stmt.stmt_id = self._connection.get_next_statement_id()
        return stmt

    def add(self, *values):
        """Adds a list of documents to a collection.

        Args:
            *values: The document list to be added into the collection.

        Returns:
            mysqlx.AddStatement: AddStatement object.
        """
        return AddStatement(self).add(*values)

    def remove(self, condition):
        """Removes documents based on the ``condition``.

        Args:
            condition (str): The string with the filter expression of the
                             documents to be removed.

        Returns:
            mysqlx.RemoveStatement: RemoveStatement object.

        .. versionchanged:: 8.0.12
           The ``condition`` parameter is now mandatory.
        """
        stmt = RemoveStatement(self, condition)
        stmt.stmt_id = self._connection.get_next_statement_id()
        return stmt

    def modify(self, condition):
        """Modifies documents based on the ``condition``.

        Args:
            condition (str): The string with the filter expression of the
                             documents to be modified.

        Returns:
            mysqlx.ModifyStatement: ModifyStatement object.

        .. versionchanged:: 8.0.12
           The ``condition`` parameter is now mandatory.
        """
        stmt = ModifyStatement(self, condition)
        stmt.stmt_id = self._connection.get_next_statement_id()
        return stmt

    def count(self):
        """Counts the documents in the collection.

        Returns:
            int: The total of documents in the collection.
        """
        sql = _COUNT_QUERY.format(quote_identifier(self._schema.name),
                                  quote_identifier(self._name))
        try:
            res = self._connection.execute_sql_scalar(sql)
        except OperationalError as err:
            if err.errno == ER_NO_SUCH_TABLE:
                raise OperationalError(
                    "Collection '{}' does not exist in schema '{}'"
                    "".format(self._name, self._schema.name))
            raise
        return res

    def create_index(self, index_name, fields_desc):
        """Creates a collection index.

        Args:
            index_name (str): Index name.
            fields_desc (dict): A dictionary containing the fields members that
                                constraints the index to be created. It must
                                have the form as shown in the following::

                                   {"fields": [{"field": member_path,
                                                "type": member_type,
                                                "required": member_required,
                                                "array": array,
                                                "collation": collation,
                                                "options": options,
                                                "srid": srid},
                                                # {... more members,
                                                #      repeated as many times
                                                #      as needed}
                                                ],
                                    "type": type}
        """
        return CreateCollectionIndexStatement(self, index_name, fields_desc)

    def drop_index(self, index_name):
        """Drops a collection index.

        Args:
            index_name (str): Index name.
        """
        self._connection.execute_nonquery("mysqlx", "drop_collection_index",
                                          False, {"schema": self._schema.name,
                                                  "collection": self._name,
                                                  "name": index_name})

    def replace_one(self, doc_id, doc):
        """Replaces the Document matching the document ID with a new document
        provided.

        Args:
            doc_id (str): Document ID
            doc (:class:`mysqlx.DbDoc` or `dict`): New Document
        """
        if "_id" in doc and doc["_id"] != doc_id:
            raise ProgrammingError(
                "Replacement document has an _id that is different than the "
                "matched document"
            )
        return self.modify("_id = :id").set("$", doc) \
                   .bind("id", doc_id).execute()

    def add_or_replace_one(self, doc_id, doc):
        """Upserts the Document matching the document ID with a new document
        provided.

        Args:
            doc_id (str): Document ID
            doc (:class:`mysqlx.DbDoc` or dict): New Document
        """
        if "_id" in doc and doc["_id"] != doc_id:
            raise ProgrammingError(
                "Replacement document has an _id that is different than the "
                "matched document"
            )
        if not isinstance(doc, DbDoc):
            doc = DbDoc(doc)
        return self.add(doc.copy(doc_id)).upsert(True).execute()

    def get_one(self, doc_id):
        """Returns a Document matching the Document ID.

        Args:
            doc_id (str): Document ID

        Returns:
            mysqlx.DbDoc: The Document matching the Document ID.
        """
        result = self.find("_id = :id").bind("id", doc_id).execute()
        doc = result.fetch_one()
        self._connection.fetch_active_result()
        return doc

    def remove_one(self, doc_id):
        """Removes a Document matching the Document ID.

        Args:
            doc_id (str): Document ID

        Returns:
            mysqlx.Result: Result object.
        """
        return self.remove("_id = :id").bind("id", doc_id).execute()


class Table(DatabaseObject):
    """Represents a database table on a schema.

    Provides access to the table through standard INSERT/SELECT/UPDATE/DELETE
    statements.

    Args:
        schema (mysqlx.Schema): The Schema object.
        name (str): The table name.
    """

    def exists_in_database(self):
        """Verifies if this object exists in the database.

        Returns:
            bool: `True` if object exists in database.
        """
        sql = _COUNT_TABLES_QUERY.format(escape(self._schema.name),
                                         escape(self._name))
        return self._connection.execute_sql_scalar(sql) == 1

    def select(self, *fields):
        """Creates a new :class:`mysqlx.SelectStatement` object.

        Args:
            *fields: The fields to be retrieved.

        Returns:
            mysqlx.SelectStatement: SelectStatement object
        """
        stmt = SelectStatement(self, *fields)
        stmt.stmt_id = self._connection.get_next_statement_id()
        return stmt

    def insert(self, *fields):
        """Creates a new :class:`mysqlx.InsertStatement` object.

        Args:
            *fields: The fields to be inserted.

        Returns:
            mysqlx.InsertStatement: InsertStatement object
        """
        stmt = InsertStatement(self, *fields)
        stmt.stmt_id = self._connection.get_next_statement_id()
        return stmt

    def update(self):
        """Creates a new :class:`mysqlx.UpdateStatement` object.

        Returns:
            mysqlx.UpdateStatement: UpdateStatement object
        """
        stmt = UpdateStatement(self)
        stmt.stmt_id = self._connection.get_next_statement_id()
        return stmt

    def delete(self):
        """Creates a new :class:`mysqlx.DeleteStatement` object.

        Returns:
            mysqlx.DeleteStatement: DeleteStatement object

        .. versionchanged:: 8.0.12
           The ``condition`` parameter was removed.
        """
        stmt = DeleteStatement(self)
        stmt.stmt_id = self._connection.get_next_statement_id()
        return stmt

    def count(self):
        """Counts the rows in the table.

        Returns:
            int: The total of rows in the table.
        """
        sql = _COUNT_QUERY.format(quote_identifier(self._schema.name),
                                  quote_identifier(self._name))
        try:
            res = self._connection.execute_sql_scalar(sql)
        except OperationalError as err:
            if err.errno == ER_NO_SUCH_TABLE:
                raise OperationalError(
                    "Table '{}' does not exist in schema '{}'"
                    "".format(self._name, self._schema.name))
            raise
        return res

    def is_view(self):
        """Determine if the underlying object is a view or not.

        Returns:
            bool: `True` if the underlying object is a view.
        """
        sql = _COUNT_VIEWS_QUERY.format(escape(self._schema.name),
                                        escape(self._name))
        return self._connection.execute_sql_scalar(sql) == 1


class View(Table):
    """Represents a database view on a schema.

    Provides a mechanism for creating, alter and drop views.

    Args:
        schema (mysqlx.Schema): The Schema object.
        name (str): The table name.
    """

    def exists_in_database(self):
        """Verifies if this object exists in the database.

        Returns:
            bool: `True` if object exists in database.
        """
        sql = _COUNT_VIEWS_QUERY.format(escape(self._schema.name),
                                        escape(self._name))
        return self._connection.execute_sql_scalar(sql) == 1

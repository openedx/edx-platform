# Copyright (c) 2020, 2021, Oracle and/or its affiliates.
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

from collections import namedtuple

import sqlparse

from mysql.connector.constants import FieldType

from django import VERSION as DJANGO_VERSION
from django.db.backends.base.introspection import (
    BaseDatabaseIntrospection, FieldInfo as BaseFieldInfo, TableInfo,
)
from django.db.models import Index
from django.utils.datastructures import OrderedSet

FieldInfo = namedtuple(
    'FieldInfo',
    BaseFieldInfo._fields + ('extra', 'is_unsigned', 'has_json_constraint')
)
if DJANGO_VERSION < (3, 2, 0):
    InfoLine = namedtuple(
        'InfoLine',
        'col_name data_type max_len num_prec num_scale extra column_default '
        'is_unsigned'
    )
else:
    InfoLine = namedtuple(
        'InfoLine',
        'col_name data_type max_len num_prec num_scale extra column_default '
        'collation is_unsigned'
    )


class DatabaseIntrospection(BaseDatabaseIntrospection):

    data_types_reverse = {
        FieldType.BLOB: 'TextField',
        FieldType.DECIMAL: 'DecimalField',
        FieldType.NEWDECIMAL: 'DecimalField',
        FieldType.DATE: 'DateField',
        FieldType.DATETIME: 'DateTimeField',
        FieldType.DOUBLE: 'FloatField',
        FieldType.FLOAT: 'FloatField',
        FieldType.INT24: 'IntegerField',
        FieldType.LONG: 'IntegerField',
        FieldType.LONGLONG: 'BigIntegerField',
        FieldType.SHORT: 'SmallIntegerField',
        FieldType.STRING: 'CharField',
        FieldType.TIME: 'TimeField',
        FieldType.TIMESTAMP: 'DateTimeField',
        FieldType.TINY: 'IntegerField',
        FieldType.TINY_BLOB: 'TextField',
        FieldType.MEDIUM_BLOB: 'TextField',
        FieldType.LONG_BLOB: 'TextField',
        FieldType.VAR_STRING: 'CharField',
    }

    def get_field_type(self, data_type, description):
        field_type = super().get_field_type(data_type, description)
        if 'auto_increment' in description.extra:
            if field_type == 'IntegerField':
                return 'AutoField'
            elif field_type == 'BigIntegerField':
                return 'BigAutoField'
            elif field_type == 'SmallIntegerField':
                return 'SmallAutoField'
        if description.is_unsigned:
            if field_type == 'BigIntegerField':
                return 'PositiveBigIntegerField'
            elif field_type == 'IntegerField':
                return 'PositiveIntegerField'
            elif field_type == 'SmallIntegerField':
                return 'PositiveSmallIntegerField'
        # JSON data type is an alias for LONGTEXT in MariaDB, use check
        # constraints clauses to introspect JSONField.
        if description.has_json_constraint:
            return 'JSONField'
        return field_type

    def get_table_list(self, cursor):
        """Return a list of table and view names in the current database."""
        cursor.execute("SHOW FULL TABLES")
        return [TableInfo(row[0], {'BASE TABLE': 't', 'VIEW': 'v'}.get(row[1]))
                for row in cursor.fetchall()]

    def get_table_description(self, cursor, table_name):
        """
        Return a description of the table with the DB-API cursor.description
        interface."
        """
        json_constraints = {}
        # A default collation for the given table.
        cursor.execute("""
            SELECT  table_collation
            FROM    information_schema.tables
            WHERE   table_schema = DATABASE()
            AND     table_name = %s
        """, [table_name])
        row = cursor.fetchone()
        default_column_collation = row[0] if row else ''
        # information_schema database gives more accurate results for some figures:
        # - varchar length returned by cursor.description is an internal length,
        #   not visible length (#5725)
        # - precision and scale (for decimal fields) (#5014)
        # - auto_increment is not available in cursor.description
        if DJANGO_VERSION < (3, 2, 0):
            cursor.execute("""
                SELECT
                    column_name, data_type, character_maximum_length,
                    numeric_precision, numeric_scale, extra, column_default,
                    CASE
                        WHEN column_type LIKE '%% unsigned' THEN 1
                        ELSE 0
                    END AS is_unsigned
                FROM information_schema.columns
                WHERE table_name = %s AND table_schema = DATABASE()
            """, [table_name])
        else:
            cursor.execute("""
                SELECT
                    column_name, data_type, character_maximum_length,
                    numeric_precision, numeric_scale, extra, column_default,
                    CASE
                        WHEN collation_name = %s THEN NULL
                        ELSE collation_name
                    END AS collation_name,
                    CASE
                        WHEN column_type LIKE '%% unsigned' THEN 1
                        ELSE 0
                    END AS is_unsigned
                FROM information_schema.columns
                WHERE table_name = %s AND table_schema = DATABASE()
            """, [default_column_collation, table_name])
        field_info = {line[0]: InfoLine(*line) for line in cursor.fetchall()}

        cursor.execute("SELECT * FROM %s LIMIT 1" % self.connection.ops.quote_name(table_name))

        def to_int(i):
            return int(i) if i is not None else i

        fields = []
        for line in cursor.description:
            info = field_info[line[0]]
            if DJANGO_VERSION < (3, 2, 0):
                fields.append(FieldInfo(
                    *line[:3],
                    to_int(info.max_len) or line[3],
                    to_int(info.num_prec) or line[4],
                    to_int(info.num_scale) or line[5],
                    line[6],
                    info.column_default,
                    info.extra,
                    info.is_unsigned,
                    line[0] in json_constraints
                ))
            else:
                fields.append(FieldInfo(
                    *line[:3],
                    to_int(info.max_len) or line[3],
                    to_int(info.num_prec) or line[4],
                    to_int(info.num_scale) or line[5],
                    line[6],
                    info.column_default,
                    info.collation,
                    info.extra,
                    info.is_unsigned,
                    line[0] in json_constraints,
                ))
        return fields

    def get_indexes(self, cursor, table_name):
        cursor.execute("SHOW INDEX FROM {0}"
                       "".format(self.connection.ops.quote_name(table_name)))
        # Do a two-pass search for indexes: on first pass check which indexes
        # are multicolumn, on second pass check which single-column indexes
        # are present.
        rows = list(cursor.fetchall())
        multicol_indexes = set()
        for row in rows:
            if row[3] > 1:
                multicol_indexes.add(row[2])
        indexes = {}
        for row in rows:
            if row[2] in multicol_indexes:
                continue
            if row[4] not in indexes:
                indexes[row[4]] = {'primary_key': False, 'unique': False}
            # It's possible to have the unique and PK constraints in
            # separate indexes.
            if row[2] == 'PRIMARY':
                indexes[row[4]]['primary_key'] = True
            if not row[1]:
                indexes[row[4]]['unique'] = True
        return indexes

    def get_primary_key_column(self, cursor, table_name):
        """
        Returns the name of the primary key column for the given table
        """
        for column in self.get_indexes(cursor, table_name).items():
            if column[1]['primary_key']:
                return column[0]
        return None

    def get_sequences(self, cursor, table_name, table_fields=()):
        for field_info in self.get_table_description(cursor, table_name):
            if 'auto_increment' in field_info.extra:
                # MySQL allows only one auto-increment column per table.
                return [{'table': table_name, 'column': field_info.name}]
        return []

    def get_relations(self, cursor, table_name):
        """
        Return a dictionary of {field_name: (field_name_other_table, other_table)}
        representing all relationships to the given table.
        """
        constraints = self.get_key_columns(cursor, table_name)
        relations = {}
        for my_fieldname, other_table, other_field in constraints:
            relations[my_fieldname] = (other_field, other_table)
        return relations

    def get_key_columns(self, cursor, table_name):
        """
        Return a list of (column_name, referenced_table_name, referenced_column_name)
        for all key columns in the given table.
        """
        key_columns = []
        cursor.execute("""
            SELECT column_name, referenced_table_name, referenced_column_name
            FROM information_schema.key_column_usage
            WHERE table_name = %s
                AND table_schema = DATABASE()
                AND referenced_table_name IS NOT NULL
                AND referenced_column_name IS NOT NULL""", [table_name])
        key_columns.extend(cursor.fetchall())
        return key_columns

    def get_storage_engine(self, cursor, table_name):
        """
        Retrieve the storage engine for a given table. Return the default
        storage engine if the table doesn't exist.
        """
        cursor.execute(
            "SELECT engine "
            "FROM information_schema.tables "
            "WHERE table_name = %s", [table_name])
        result = cursor.fetchone()
        if not result:
            return self.connection.features._mysql_storage_engine
        return result[0]

    def get_constraints(self, cursor, table_name):
        """
        Retrieve any constraints or keys (unique, pk, fk, check, index) across
        one or more columns.
        """
        constraints = {}
        # Get the actual constraint names and columns
        name_query = """
            SELECT kc.`constraint_name`, kc.`column_name`,
                kc.`referenced_table_name`, kc.`referenced_column_name`
            FROM information_schema.key_column_usage AS kc
            WHERE
                kc.table_schema = DATABASE() AND
                kc.table_name = %s
            ORDER BY kc.`ordinal_position`
        """
        cursor.execute(name_query, [table_name])
        for constraint, column, ref_table, ref_column in cursor.fetchall():
            if constraint not in constraints:
                constraints[constraint] = {
                    'columns': OrderedSet(),
                    'primary_key': False,
                    'unique': False,
                    'index': False,
                    'check': False,
                    'foreign_key': (ref_table, ref_column) if ref_column else None,
                }
                if self.connection.features.supports_index_column_ordering:
                    constraints[constraint]['orders'] = []
            constraints[constraint]['columns'].add(column)
        # Now get the constraint types
        type_query = """
            SELECT c.constraint_name, c.constraint_type
            FROM information_schema.table_constraints AS c
            WHERE
                c.table_schema = DATABASE() AND
                c.table_name = %s
        """
        cursor.execute(type_query, [table_name])
        for constraint, kind in cursor.fetchall():
            if kind.lower() == "primary key":
                constraints[constraint]['primary_key'] = True
                constraints[constraint]['unique'] = True
            elif kind.lower() == "unique":
                constraints[constraint]['unique'] = True
        # Add check constraints.
        if self.connection.features.can_introspect_check_constraints:
            unnamed_constraints_index = 0
            columns = {info.name for info in self.get_table_description(cursor, table_name)}
            type_query = """
                SELECT cc.constraint_name, cc.check_clause
                FROM
                    information_schema.check_constraints AS cc,
                    information_schema.table_constraints AS tc
                WHERE
                    cc.constraint_schema = DATABASE() AND
                    tc.table_schema = cc.constraint_schema AND
                    cc.constraint_name = tc.constraint_name AND
                    tc.constraint_type = 'CHECK' AND
                    tc.table_name = %s
            """
            cursor.execute(type_query, [table_name])
            for constraint, check_clause in cursor.fetchall():
                constraint_columns = self._parse_constraint_columns(check_clause, columns)
                # Ensure uniqueness of unnamed constraints. Unnamed unique
                # and check columns constraints have the same name as
                # a column.
                if set(constraint_columns) == {constraint}:
                    unnamed_constraints_index += 1
                    constraint = '__unnamed_constraint_%s__' % unnamed_constraints_index
                constraints[constraint] = {
                    'columns': constraint_columns,
                    'primary_key': False,
                    'unique': False,
                    'index': False,
                    'check': True,
                    'foreign_key': None,
                }
        # Now add in the indexes
        cursor.execute("SHOW INDEX FROM %s" % self.connection.ops.quote_name(table_name))
        for table, non_unique, index, colseq, column, order, type_ in [
            x[:6] + (x[10],) for x in cursor.fetchall()
        ]:
            if index not in constraints:
                constraints[index] = {
                    'columns': OrderedSet(),
                    'primary_key': False,
                    'unique': False,
                    'check': False,
                    'foreign_key': None,
                }
                if self.connection.features.supports_index_column_ordering:
                    constraints[index]['orders'] = []
            constraints[index]['index'] = True
            constraints[index]['type'] = Index.suffix if type_ == 'BTREE' else type_.lower()
            constraints[index]['columns'].add(column)
            if self.connection.features.supports_index_column_ordering:
                constraints[index]['orders'].append('DESC' if order == 'D' else 'ASC')
        # Convert the sorted sets to lists
        for constraint in constraints.values():
            constraint['columns'] = list(constraint['columns'])
        return constraints

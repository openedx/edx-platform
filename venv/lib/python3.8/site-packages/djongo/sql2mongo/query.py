"""
Module with constants and mappings to build MongoDB queries from
SQL constructors.
"""
import abc
import re
from logging import getLogger
from typing import Optional, Dict, List, Union as U, Sequence, Set
from dataclasses import dataclass, field as dataclass_field
from pymongo import MongoClient
from pymongo import ReturnDocument
from pymongo.command_cursor import CommandCursor
from pymongo.cursor import Cursor as BasicCursor
from pymongo.database import Database
from pymongo.errors import OperationFailure, CollectionInvalid
from sqlparse import parse as sqlparse
from sqlparse import tokens
from sqlparse.sql import (
    Identifier, Parenthesis,
    Where,
    Statement)

from ..exceptions import SQLDecodeError, MigrationError, print_warn
from .functions import SQLFunc
from .sql_tokens import (SQLToken, SQLStatement, SQLIdentifier,
                         AliasableToken, SQLConstIdentifier, SQLColumnDef, SQLColumnConstraint)
from .converters import (
    ColumnSelectConverter, AggColumnSelectConverter, FromConverter, WhereConverter,
    AggWhereConverter, InnerJoinConverter, OuterJoinConverter, LimitConverter, AggLimitConverter, OrderConverter,
    SetConverter, AggOrderConverter, DistinctConverter, NestedInQueryConverter, GroupbyConverter, OffsetConverter,
    AggOffsetConverter, HavingConverter)

from djongo import base
logger = getLogger(__name__)


@dataclass
class TokenAlias:
    alias2token: Dict[str, U[AliasableToken,
                             SQLFunc,
                             SQLIdentifier]] = dataclass_field(default_factory=dict)
    token2alias: Dict[U[AliasableToken,
                        SQLFunc,
                        SQLIdentifier], str] = dataclass_field(default_factory=dict)
    aliased_names: Set[str] = dataclass_field(default_factory=set)


class BaseQuery(abc.ABC):
    def __init__(self,
                 db: Database,
                 connection_properties: 'base.DjongoClient',
                 statement: Statement,
                 params: Sequence):
        self.statement = statement
        self.db = db
        self.connection_properties = connection_properties
        self.params = params
        self.token_alias = TokenAlias()
        self.nested_query: Optional[NestedInQueryConverter] = None
        self.left_table: Optional[str] = None
        self._cursor = None
        self.parse()

    def __iter__(self):
        return
        yield

    @abc.abstractmethod
    def parse(self):
        raise NotImplementedError

    @abc.abstractmethod
    def execute(self):
        raise NotImplementedError


DMLQuery = BaseQuery


class DDLQuery(BaseQuery):

    @abc.abstractmethod
    def __init__(self, *args):
        super().__init__(*args)

    def execute(self):
        return 


class DQLQuery(BaseQuery):

    def execute(self):
        return

    @abc.abstractmethod
    def count(self):
        raise NotImplementedError


class SelectQuery(DQLQuery):

    def __init__(self, *args):
        self.selected_columns: Optional[ColumnSelectConverter] = None
        self.where: Optional[WhereConverter] = None
        self.joins: List[
            U[InnerJoinConverter, OuterJoinConverter]
        ] = []
        self.order: Optional[OrderConverter] = None
        self.offset: Optional[OffsetConverter] = None
        self.limit: Optional[LimitConverter] = None
        self.distinct: Optional[DistinctConverter] = None
        self.groupby: Optional[GroupbyConverter] = None
        self.having: Optional[HavingConverter] = None

        self._cursor: Optional[U[BasicCursor, CommandCursor]] = None
        super().__init__(*args)

    def parse(self):
        statement = SQLStatement(self.statement)

        for tok in statement:
            if tok.match(tokens.DML, 'SELECT'):
                self.selected_columns = ColumnSelectConverter(self, statement)

            elif tok.match(tokens.Keyword, 'FROM'):
                FromConverter(self, statement)

            elif tok.match(tokens.Keyword, 'LIMIT'):
                self.limit = LimitConverter(self, statement)

            elif tok.match(tokens.Keyword, 'ORDER'):
                self.order = OrderConverter(self, statement)

            elif tok.match(tokens.Keyword, 'OFFSET'):
                self.offset = OffsetConverter(self, statement)

            elif tok.match(tokens.Keyword, 'INNER JOIN'):
                converter = InnerJoinConverter(self, statement)
                self.joins.append(converter)

            elif tok.match(tokens.Keyword, 'LEFT OUTER JOIN'):
                converter = OuterJoinConverter(self, statement)
                self.joins.append(converter)

            elif tok.match(tokens.Keyword, 'GROUP'):
                self.groupby = GroupbyConverter(self, statement)

            elif tok.match(tokens.Keyword, 'HAVING'):
                self.having = HavingConverter(self, statement)

            elif isinstance(tok, Where):
                self.where = WhereConverter(self, statement)

            else:
                raise SQLDecodeError(f'Unknown keyword: {tok}')

    def __iter__(self):

        if self._cursor is None:
            self._cursor = self._get_cursor()

        cursor = self._cursor
        if not cursor.alive:
            return

        for doc in cursor:
            yield self._align_results(doc)
        return

    def count(self):

        if self._cursor is None:
            self._cursor = self._get_cursor()
        return len(list(self._cursor))
        # if isinstance(self._cursor, BasicCursor):
        #     return self._cursor.count()
        # else:
        #     return len(list(self._cursor))

    def _needs_aggregation(self):
        if (self.nested_query
                or self.joins
                or self.distinct
                or self.groupby):
            return True
        if any(isinstance(sql_token, (SQLFunc, SQLConstIdentifier))
               for sql_token in self.selected_columns.sql_tokens):
            return True
        return False

    def _make_pipeline(self):
        pipeline = []
        for join in self.joins:
            pipeline.extend(join.to_mongo())

        if self.nested_query:
            pipeline.extend(self.nested_query.to_mongo())

        if self.where:
            self.where.__class__ = AggWhereConverter
            pipeline.append(self.where.to_mongo())

        if self.groupby:
            pipeline.extend(self.groupby.to_mongo())

        if self.having:
            pipeline.append(self.having.to_mongo())

        if self.distinct:
            pipeline.extend(self.distinct.to_mongo())

        if self.order:
            self.order.__class__ = AggOrderConverter
            pipeline.append(self.order.to_mongo())

        if self.offset:
            self.offset.__class__ = AggOffsetConverter
            pipeline.append(self.offset.to_mongo())

        if self.limit:
            self.limit.__class__ = AggLimitConverter
            pipeline.append(self.limit.to_mongo())

        if self._needs_column_selection():
            self.selected_columns.__class__ = AggColumnSelectConverter
            pipeline.extend(self.selected_columns.to_mongo())

        return pipeline

    def _needs_column_selection(self):
        return not(self.distinct or self.groupby) and self.selected_columns

    def _get_cursor(self):
        if self._needs_aggregation():
            pipeline = self._make_pipeline()
            cur = self.db[self.left_table].aggregate(pipeline)
            logger.debug(f'Aggregation query: {pipeline}')
        else:
            kwargs = {}
            if self.where:
                kwargs.update(self.where.to_mongo())

            if self.selected_columns:
                kwargs.update(self.selected_columns.to_mongo())

            if self.limit:
                kwargs.update(self.limit.to_mongo())

            if self.order:
                kwargs.update(self.order.to_mongo())
            
            if self.offset:
                kwargs.update(self.offset.to_mongo())

            cur = self.db[self.left_table].find(**kwargs)
            logger.debug(f'Find query: {kwargs}')

        return cur

    def _align_results(self, doc):
        ret = []
        if self.distinct:
            sql_tokens = self.distinct.sql_tokens
        else:
            sql_tokens = self.selected_columns.sql_tokens

        for selected in sql_tokens:
            if isinstance(selected, SQLIdentifier):
                if selected.table == self.left_table:
                    try:
                        ret.append(doc[selected.column])
                    except KeyError:
                        if self.connection_properties.enforce_schema:
                            raise MigrationError(selected.column)
                        ret.append(None)
                else:
                    try:
                        ret.append(doc[selected.table][selected.column])
                    except KeyError:
                        if self.connection_properties.enforce_schema:
                            raise MigrationError(selected.column)
                        ret.append(None)
            else:
                ret.append(doc[selected.alias])

        return tuple(ret)


class UpdateQuery(DMLQuery):

    def __init__(self, *args):
        self.selected_table: Optional[ColumnSelectConverter] = None
        self.set_columns: Optional[SetConverter] = None
        self.where: Optional[WhereConverter] = None
        self.result = None
        self.kwargs = None
        super().__init__(*args)

    def count(self):
        return self.result.matched_count

    def parse(self):

        statement = SQLStatement(self.statement)

        for tok in statement:
            if tok.match(tokens.DML, 'UPDATE'):
                c = ColumnSelectConverter(self, statement)
                self.left_table = c.sql_tokens[0].table

            elif tok.match(tokens.Keyword, 'SET'):
                c = self.set_columns = SetConverter(self, statement)

            elif isinstance(tok, Where):
                c = self.where = WhereConverter(self, statement)

            else:
                raise SQLDecodeError

        self.kwargs = {}
        if self.where:
            self.kwargs.update(self.where.to_mongo())

        self.kwargs.update(self.set_columns.to_mongo())

    def execute(self):
        db = self.db
        self.result = db[self.left_table].update_many(**self.kwargs)
        logger.debug(f'update_many: {self.result.modified_count}, matched: {self.result.matched_count}')


class InsertQuery(DMLQuery):

    def __init__(self,
                 result_ref: 'Query',
                 *args):
        self._result_ref = result_ref
        self._cols = None
        self._values = []
        super().__init__(*args)

    def _table(self, statement: SQLStatement):
        tok = statement.next()
        collection = tok.get_name()
        if collection not in self.connection_properties.cached_collections:
            if self.connection_properties.enforce_schema:
                raise MigrationError(f'Table {collection} does not exist in database')
            self.connection_properties.cached_collections.add(collection)

        self.left_table = collection

    def _columns(self, statement: SQLStatement):
        tok = statement.next()
        self._cols = [token.column for token in SQLToken.tokens2sql(tok[1], self)]

    def _fill_values(self, statement: SQLStatement):
        for tok in statement:
            if isinstance(tok, Parenthesis):
                placeholder = SQLToken.token2sql(tok, self)
                values = []
                for index in placeholder:
                    if isinstance(index, int):
                        values.append(self.params[index])
                    else:
                        values.append(index)
                self._values.append(values)
            elif not tok.match(tokens.Keyword, 'VALUES'):
                raise SQLDecodeError

    def execute(self):
        docs = []
        num = len(self._values)

        auto = self.db['__schema__'].find_one_and_update(
            {
                'name': self.left_table,
                'auto': {
                    '$exists': True
                }
            },
            {'$inc': {'auto.seq': num}},
            return_document=ReturnDocument.AFTER
        )

        for i, val in enumerate(self._values):
            ins = {}
            if auto:
                for name in auto['auto']['field_names']:
                    ins[name] = auto['auto']['seq'] - num + i + 1
            for _field, value in zip(self._cols, val):
                if (auto and _field in auto['auto']['field_names']
                        and value == 'DEFAULT'):
                    continue
                ins[_field] = value
            docs.append(ins)

        res = self.db[self.left_table].insert_many(docs, ordered=False)
        if auto:
            self._result_ref.last_row_id = auto['auto']['seq']
        else:
            self._result_ref.last_row_id = res.inserted_ids[-1]
        logger.debug('inserted ids {}'.format(res.inserted_ids))

    def parse(self):
        statement = SQLStatement(self.statement)
        # Skip to table name
        statement.skip(4)
        self._table(statement)
        self._columns(statement)
        self._fill_values(statement)


class AlterQuery(DDLQuery):

    def __init__(self, *args):
        self._iden_name = None
        self._old_name = None
        self._new_name = None
        self._new_name = None
        self._default = None
        self._type_code = None
        self._cascade = None
        self._null = None

        super().__init__(*args)

    def parse(self):
        statement = SQLStatement(self.statement)
        statement.skip(2)

        for tok in statement:
            if tok.match(tokens.Keyword, 'TABLE'):
                self._table(statement)
            elif tok.match(tokens.Keyword, 'ADD'):
                self._add(statement)
            elif tok.match(tokens.Keyword, 'FLUSH'):
                self.execute = self._flush
            elif tok.match(tokens.Keyword.DDL, 'DROP'):
                self._drop(statement)
            elif tok.match(tokens.Keyword.DDL, 'ALTER'):
                self._alter(statement)
            elif tok.match(tokens.Keyword, 'RENAME'):
                self._rename(statement)
            else:
                raise SQLDecodeError(f'Unknown token {tok}')

    def _rename(self, statement: SQLStatement):
        column = False
        to = False
        for tok in statement:
            if tok.match(tokens.Keyword, 'COLUMN'):
                self.execute = self._rename_column
                column = True
            if tok.match(tokens.Keyword, 'TO'):
                to = True
            elif isinstance(tok, Identifier):
                if not to:
                    self._old_name = tok.get_real_name()
                else:
                    self._new_name = tok.get_real_name()

        if not column:
            # Rename table
            self.execute = self._rename_collection

    def _rename_column(self):
        self.db[self.left_table].update(
            {},
            {
                '$rename': {
                    self._old_name: self._new_name
                }
            },
            multi=True
        )

    def _rename_collection(self):
        self.db[self.left_table].rename(self._new_name)

    def _alter(self, statement: SQLStatement):
        self.execute = lambda: None
        feature = ''

        for tok in statement:
            if isinstance(tok, Identifier):
                pass
            elif tok.ttype == tokens.Name.Placeholder:
                pass
            elif tok.match(tokens.Keyword, (
                    'NOT NULL', 'NULL', 'COLUMN',
            )):
                feature += str(tok) + ' '
            elif tok.match(tokens.Keyword.DDL, 'DROP'):
                feature += 'DROP '
            elif tok.match(tokens.Keyword, 'DEFAULT'):
                feature += 'DEFAULT '
            elif tok.match(tokens.Keyword, 'SET'):
                feature += 'SET '
            else:
                raise SQLDecodeError(f'Unknown token: {tok}')

        print_warn(feature)

    def _flush(self):
        self.db[self.left_table].delete_many({})

    def _table(self, statement: SQLStatement):
        tok = statement.next()
        if not tok:
            raise SQLDecodeError
        self.left_table = SQLToken.token2sql(tok, self).table

    def _drop(self, statement: SQLStatement):

        for tok in statement:
            if tok.match(tokens.Keyword, 'CASCADE'):
                print_warn('DROP CASCADE')
            elif isinstance(tok, Identifier):
                self._iden_name = tok.get_real_name()
            elif tok.match(tokens.Keyword, 'INDEX'):
                self.execute = self._drop_index
            elif tok.match(tokens.Keyword, 'CONSTRAINT'):
                pass
            elif tok.match(tokens.Keyword, 'COLUMN'):
                self.execute = self._drop_column
            else:
                raise SQLDecodeError

    def _drop_index(self):
        self.db[self.left_table].drop_index(self._iden_name)

    def _drop_column(self):
        self.db[self.left_table].update(
            {},
            {
                '$unset': {
                    self._iden_name: ''
                }
            },
            multi=True
        )
        self.db['__schema__'].update(
            {'name': self.left_table},
            {
                '$unset': {
                    f'fields.{self._iden_name}': ''
                }
            }
        )

    def _add(self, statement: SQLStatement):
        for tok in statement:
            if tok.match(tokens.Keyword, (
                'CONSTRAINT', 'KEY', 'REFERENCES',
                'NOT NULL', 'NULL'
            )):
                print_warn(f'schema validation using {tok}')

            elif tok.match(tokens.Name.Builtin, '.*', regex=True):
                print_warn('column type validation')
                self._type_code = str(tok)

            elif tok.match(tokens.Keyword, 'double'):
                print_warn('column type validation')
                self._type_code = str(tok)

            elif isinstance(tok, Identifier):
                self._iden_name = tok.get_real_name()

            elif isinstance(tok, Parenthesis):
                self.field_dir = [
                    (field.strip(' "'), 1)
                    for field in tok.value.strip('()').split(',')
                ]

            elif tok.match(tokens.Keyword, 'DEFAULT'):
                tok = statement.next()
                i = SQLToken.placeholder_index(tok)
                self._default = self.params[i]

            elif tok.match(tokens.Keyword, 'UNIQUE'):
                if self.execute == self._add_column:
                    self.field_dir = [(self._iden_name, 1)]
                self.execute = self._unique

            elif tok.match(tokens.Keyword, 'INDEX'):
                self.execute = self._index

            elif tok.match(tokens.Keyword, 'FOREIGN'):
                self.execute = self._fk

            elif tok.match(tokens.Keyword, 'COLUMN'):
                self.execute = self._add_column

            elif isinstance(tok, Where):
                print_warn('partial indexes')

            else:
                raise SQLDecodeError(err_key=tok.value,
                                     err_sub_sql=statement)

    def _add_column(self):
        self.db[self.left_table].update(
            {
                '$or': [
                    {self._iden_name: {'$exists': False}},
                    {self._iden_name: None}
                ]
            },
            {
                '$set': {
                    self._iden_name: self._default
                }
            },
            multi=True
        )
        self.db['__schema__'].update(
            {'name': self.left_table},
            {
                '$set': {
                    f'fields.{self._iden_name}': {
                        'type_code': self._type_code
                    }
                }
            }
        )

    def _index(self):
        self.db[self.left_table].create_index(
            self.field_dir,
            name=self._iden_name)

    def _unique(self):
        self.db[self.left_table].create_index(
            self.field_dir,
            unique=True,
            name=self._iden_name)

    def _fk(self):
        pass


class CreateQuery(DDLQuery):

    def __init__(self, *args):
        super().__init__(*args)

    def _create_table(self, statement):
        if '__schema__' not in self.connection_properties.cached_collections:
            self.db.create_collection('__schema__')
            self.connection_properties.cached_collections.add('__schema__')
            self.db['__schema__'].create_index('name', unique=True)
            self.db['__schema__'].create_index('auto')

        tok = statement.next()
        table = SQLToken.token2sql(tok, self).table
        try:
            self.db.create_collection(table)
        except CollectionInvalid:
            if self.connection_properties.enforce_schema:
                raise
            else:
                return

        logger.debug('Created table: {}'.format(table))

        tok = statement.next()
        if not isinstance(tok, Parenthesis):
            raise SQLDecodeError(f'Unexpected sql syntax'
                                 f' for column definition: {statement}')

        if statement.next():
            raise SQLDecodeError(f'Unexpected sql syntax'
                                 f' for column definition: {statement}')

        _filter = {
            'name': table
        }
        _set = {}
        push = {}
        update = {}

        for col in SQLColumnDef.sql2col_defs(tok.value):
            if isinstance(col, SQLColumnConstraint):
                print_warn('column CONSTRAINTS')
            else:
                field = col.name
                if field == '_id':
                    continue

                _set[f'fields.{field}'] = {
                    'type_code': col.data_type
                }

                if SQLColumnDef.autoincrement in col.col_constraints:
                    try:
                        push['auto.field_names']['$each'].append(field)
                    except KeyError:
                        push['auto.field_names'] = {
                            '$each': [field]
                        }
                    _set['auto.seq'] = 0

                if SQLColumnDef.primarykey in col.col_constraints:
                    self.db[table].create_index(field, unique=True, name='__primary_key__')

                if SQLColumnDef.unique in col.col_constraints:
                    self.db[table].create_index(field, unique=True)

                if (SQLColumnDef.not_null in col.col_constraints or
                        SQLColumnDef.null in col.col_constraints):
                    print_warn('NULL, NOT NULL column validation check')

        if _set:
            update['$set'] = _set
        if push:
            update['$push'] = push
        if update:
            self.db['__schema__'].update_one(
                filter=_filter,
                update=update,
                upsert=True
            )

    def parse(self):
        statement = SQLStatement(self.statement)
        statement.skip(2)
        tok = statement.next()
        if tok.match(tokens.Keyword, 'TABLE'):
            self._create_table(statement)
        elif tok.match(tokens.Keyword, 'DATABASE'):
            pass
        else:
            logger.debug('Not supported {}'.format(self.statement))
            raise SQLDecodeError


class DeleteQuery(DMLQuery):

    def __init__(self, *args):
        self.result = None
        self.kw = None
        super().__init__(*args)

    def parse(self):
        statement = SQLStatement(self.statement)
        self.kw = kw = {'filter': {}}
        statement.skip(4)
        sql_token = SQLToken.token2sql(statement.next(), self)
        self.left_table = sql_token.table

        tok = statement.next()
        if isinstance(tok, Where):
            where = WhereConverter(self, statement)
            kw.update(where.to_mongo())

    def execute(self):
        db_con = self.db
        self.result = db_con[self.left_table].delete_many(**self.kw)
        logger.debug('delete_many: {}'.format(self.result.deleted_count))

    def count(self):
        return self.result.deleted_count


class Query:

    def __init__(self,
                 client_connection: MongoClient,
                 db_connection: Database,
                 connection_properties: 'base.DjongoClient',
                 sql: str,
                 params: Optional[Sequence]):

        self._params = params
        self.db = db_connection
        self.cli_con = client_connection
        self.connection_properties = connection_properties
        self._params_index_count = -1
        self._sql = re.sub(r'%s', self._param_index, sql)
        self.last_row_id = None
        self._result_generator = None

        self._query = self.parse()

    def count(self):
        return self._query.count()

    def close(self):
        if self._query and self._query._cursor:
            self._query._cursor.close()

    def __next__(self):
        if self._result_generator is None:
            self._result_generator = iter(self)

        result = next(self._result_generator)
        logger.debug(f'Result: {result}')
        return result

    next = __next__

    def __iter__(self):
        if self._query is None:
            return

        try:
            yield from iter(self._query)

        except MigrationError:
            raise

        except OperationFailure as e:
            import djongo
            exe = SQLDecodeError(
                f'FAILED SQL: {self._sql}\n' 
                f'Params: {self._params}\n'
                f'Pymongo error: {e.details}\n'
                f'Version: {djongo.__version__}'
            )
            raise exe from e

        except Exception as e:
            import djongo
            exe = SQLDecodeError(
                f'FAILED SQL: {self._sql}\n'
                f'Params: {self._params}\n'
                f'Version: {djongo.__version__}'
            )
            raise exe from e

    def _param_index(self, _):
        self._params_index_count += 1
        return '%({})s'.format(self._params_index_count)

    def parse(self):
        logger.debug(
            f'sql_command: {self._sql}\n'
            f'params: {self._params}'
        )
        statement = sqlparse(self._sql)

        if len(statement) > 1:
            raise SQLDecodeError(self._sql)

        statement = statement[0]
        sm_type = statement.get_type()

        try:
            handler = self.FUNC_MAP[sm_type]
        except KeyError:
            logger.debug('\n Not implemented {} {}'.format(sm_type, statement))
            raise SQLDecodeError(f'{sm_type} command not implemented for SQL {self._sql}')

        else:
            try:
                return handler(self, statement)

            except MigrationError:
                raise

            except OperationFailure as e:
                import djongo
                exe = SQLDecodeError(
                    err_sql=self._sql,
                    params=self._params,
                    version=djongo.__version__
                )
                raise exe from e

            except SQLDecodeError as e:
                import djongo
                e.err_sql = self._sql,
                e.params = self._params,
                e.version = djongo.__version__
                raise e

            except Exception as e:
                import djongo
                exe = SQLDecodeError(
                    err_sql=self._sql,
                    params=self._params,
                    version=djongo.__version__
                )
                raise exe from e

    def _alter(self, sm):
        try:
            query = AlterQuery(self.db, self.connection_properties, sm, self._params)
        except SQLDecodeError:
            logger.warning('Not implemented alter command for SQL {}'.format(self._sql))
            raise
        else:
            query.execute()
            return query

    def _create(self, sm):
        query = CreateQuery(self.db, self.connection_properties, sm, self._params)
        query.execute()
        return query

    def _drop(self, sm):
        statement = SQLStatement(sm)
        statement.skip(2)
        tok = statement.next()
        if tok.match(tokens.Keyword, 'DATABASE'):
            tok = statement.next()
            db_name = tok.get_name()
            self.cli_con.drop_database(db_name)
        elif tok.match(tokens.Keyword, 'TABLE'):
            tok = statement.next()
            table_name = tok.get_name()
            self.db.drop_collection(table_name)
        else:
            raise SQLDecodeError('statement:{}'.format(sm))

    def _update(self, sm):
        query = UpdateQuery(self.db, self.connection_properties, sm, self._params)
        query.execute()
        return query

    def _delete(self, sm):
        query = DeleteQuery(self.db, self.connection_properties, sm, self._params)
        query.execute()
        return query

    def _insert(self, sm):
        query = InsertQuery(self, self.db, self.connection_properties, sm, self._params)
        query.execute()
        return query

    def _select(self, sm):
        return SelectQuery(self.db, self.connection_properties, sm, self._params)

    FUNC_MAP = {
        'SELECT': _select,
        'UPDATE': _update,
        'INSERT': _insert,
        'DELETE': _delete,
        'CREATE': _create,
        'DROP': _drop,
        'ALTER': _alter
    }




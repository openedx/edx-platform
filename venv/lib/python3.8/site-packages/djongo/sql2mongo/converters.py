import abc
import typing
from collections import OrderedDict
from sqlparse import tokens, parse as sqlparse
from sqlparse.sql import Parenthesis
from typing import Union as U, List, Optional as O
from . import query as query_module
from .sql_tokens import SQLIdentifier, SQLConstIdentifier, SQLComparison
from .functions import SQLFunc, CountFuncAll
from .operators import WhereOp
from ..exceptions import SQLDecodeError
from .sql_tokens import SQLToken, SQLStatement


class Converter:

    @abc.abstractmethod
    def __init__(
            self,
            query: U['query_module.SelectQuery',
                     'query_module.BaseQuery'],
            statement: SQLStatement
    ):
        self.query = query
        self.statement = statement
        self.end_id = None
        self.parse()

    def parse(self):
        raise NotImplementedError

    def to_mongo(self):
        raise NotImplementedError


class ColumnSelectConverter(Converter):
    def __init__(self, query, statement):
        self.select_all = False
        self.num_columns = 0

        self.sql_tokens: List[
            U[SQLIdentifier, SQLFunc]
        ] = []
        super().__init__(query, statement)

    def parse(self):
        tok = self.statement.next()

        if tok.match(tokens.Keyword, 'DISTINCT'):
            self.query.distinct = DistinctConverter(self.query, self.statement)

        else:
            for sql_token in SQLToken.tokens2sql(tok, self.query):
                self.sql_tokens.append(sql_token)

    def to_mongo(self):
        doc = [selected.column for selected in self.sql_tokens]
        return {'projection': doc}


class AggColumnSelectConverter(ColumnSelectConverter):

    def to_mongo(self):
        project = {}

        if any(isinstance(tok, SQLFunc) for tok in self.sql_tokens):
            # A SELECT func without groupby clause still needs a groupby
            # in MongoDB
            return self._using_group_by()

        elif isinstance(self.sql_tokens[0], SQLConstIdentifier):
            project[self.sql_tokens[0].alias] = self.sql_tokens[0].to_mongo()
        else:
            for selected in self.sql_tokens:
                project[selected.field] = True

        return [{'$project': project}]

    def _using_group_by(self):
        group = {
            '_id': None
        }
        project = {
            '_id': False
        }
        for selected in self.sql_tokens:
            if isinstance(selected, SQLFunc):
                group[selected.alias] = selected.to_mongo()
                project[selected.alias] = True
            else:
                project[selected.field] = True

        pipeline = [
            {
                '$group': group
            },
            {
                '$project': project
            }
        ]

        return pipeline


class FromConverter(Converter):

    def parse(self):
        tok = self.statement.next()
        sql = SQLToken.token2sql(tok, self.query)
        self.query.left_table = sql.table


class WhereConverter(Converter):
    nested_op: 'WhereOp' = None
    op: 'WhereOp' = None

    def parse(self):
        tok = self.statement.current_token
        self.op = WhereOp(
            statement=SQLStatement(tok),
            query=self.query,
            params=self.query.params
        )

    def to_mongo(self):
        return {'filter': self.op.to_mongo()}


class AggWhereConverter(WhereConverter):

    def to_mongo(self):
        return {'$match': self.op.to_mongo()}


class JoinConverter(Converter):

    @abc.abstractmethod
    def __init__(self, *args):
        self.left_table: O[str] = None
        self.right_table: O[str] = None
        self.left_column: O[str] = None
        self.right_column: O[str] = None
        super().__init__(*args)

    def parse(self):
        tok = self.statement.next()
        sql = SQLToken.token2sql(tok, self.query)
        right_table = self.right_table = sql.table

        tok = self.statement.next()
        if not tok.match(tokens.Keyword, 'ON'):
            raise SQLDecodeError

        tok = self.statement.next()
        if isinstance(tok, Parenthesis):
            tok = tok[1]

        sql = SQLToken.token2sql(tok, self.query)
        if right_table == sql.right_table:
            self.left_table = sql.left_table
            self.left_column = sql.left_column
            self.right_column = sql.right_column
        else:
            self.left_table = sql.right_table
            self.left_column = sql.right_column
            self.right_column = sql.left_column

    def _lookup(self):
        if self.left_table == self.query.left_table:
            local_field = self.left_column
        else:
            local_field = f'{self.left_table}.{self.left_column}'

        lookup = {
            '$lookup': {
                'from': self.right_table,
                'localField': local_field,
                'foreignField': self.right_column,
                'as': self.right_table
            }
        }

        return lookup


class InnerJoinConverter(JoinConverter):

    def __init__(self, *args):
        super().__init__(*args)

    def to_mongo(self):
        if self.left_table == self.query.left_table:
            match_field = self.left_column
        else:
            match_field = f'{self.left_table}.{self.left_column}'

        lookup = self._lookup()
        pipeline = [
            {
                '$match': {
                    match_field: {
                        '$ne': None,
                        '$exists': True
                    }
                }
            },
            lookup,
            {
                '$unwind': '$' + self.right_table
            }
        ]

        return pipeline


class OuterJoinConverter(JoinConverter):

    def __init__(self, *args):
        super().__init__(*args)

    def _null_fields(self, table):
        toks = self.query.selected_columns.sql_tokens
        fields = {}
        for tok in toks:
            if not isinstance(tok, CountFuncAll) and tok.table == table:
                fields[tok.column] = None
        return fields

    def to_mongo(self):
        lookup = self._lookup()
        null_fields = self._null_fields(self.right_table)

        pipeline = [
            lookup,
            {
                '$unwind': {
                    'path': '$' + self.right_table,
                    'preserveNullAndEmptyArrays': True
                }
            },
            {
                '$addFields': {
                    self.right_table: {
                        '$ifNull': ['$' + self.right_table, null_fields]
                    }
                }
            }
        ]

        return pipeline


class LimitConverter(Converter):
    def __init__(self, *args):
        self.limit: O[int] = None
        super().__init__(*args)

    def parse(self):
        tok = self.statement.next()
        self.limit = int(tok.value)

    def to_mongo(self):
        return {'limit': self.limit}


class AggLimitConverter(LimitConverter):

    def to_mongo(self):
        return {'$limit': self.limit}


class OrderConverter(Converter):
    def __init__(self, *args):
        self.columns: List[SQLIdentifier] = []
        super().__init__(*args)

    def parse(self):
        tok = self.statement.next()
        if not tok.match(tokens.Keyword, 'BY'):
            raise SQLDecodeError

        tok = self.statement.next()
        self.columns.extend(SQLToken.tokens2sql(tok, self.query))

    def to_mongo(self):
        sort = [(tok.column, tok.order) for tok in self.columns]
        return {'sort': sort}


class SetConverter(Converter):

    def __init__(self, *args):
        self.sql_tokens: List[SQLComparison] = []
        super().__init__(*args)

    def parse(self):
        tok = self.statement.next()
        self.sql_tokens.extend(SQLToken.tokens2sql(tok, self.query))

    def to_mongo(self):
        return {
            'update': {
                '$set': {
                    sql.left_column: self.query.params[sql.rhs_indexes]
                    if sql.rhs_indexes is not None else None
                    for sql in self.sql_tokens}
            }
        }


class AggOrderConverter(OrderConverter):

    def to_mongo(self):
        sort = OrderedDict()
        for tok in self.columns:
            sort[tok.field] = tok.order

        return {'$sort': sort}


class _Tokens2Id:
    sql_tokens: List[
        U[SQLIdentifier, SQLFunc]
    ]
    query: U['query_module.SelectQuery',
             'query_module.BaseQuery']

    def to_id(self):
        _id = {}
        for iden in self.sql_tokens:
            if iden.column == iden.field:
                _id[iden.field] = f'${iden.field}'
            else:
                try:
                    _id[iden.table][iden.column] = f'${iden.field}'
                except KeyError:
                    _id[iden.table] = {iden.column: f'${iden.field}'}
            # if iden.table == self.query.left_table:
            #     _id[iden.column] = f'${iden.column}'
            # else:
            #     mongo_field = f'${iden.table}.{iden.column}'
            #     try:
            #         _id[iden.table][iden.column] = mongo_field
            #     except KeyError:
            #         _id[iden.table] = {iden.column: mongo_field}

        return _id


class DistinctConverter(ColumnSelectConverter, _Tokens2Id):
    def __init__(self, *args):
        super().__init__(*args)

    def to_mongo(self):
        _id = self.to_id()

        return [
            {
                '$group': {
                    '_id': _id
                }
            },
            {
                '$replaceRoot': {
                    'newRoot': '$_id'
                }
            }
        ]


class NestedInQueryConverter(Converter):

    def __init__(self, token, *args):
        self._token = token
        self._in_query: O['query_module.SelectQuery'] = None
        super().__init__(*args)

    def parse(self):
        from .query import SelectQuery

        self._in_query = SelectQuery(
            self.query.db,
            self.query.connection_properties,
            sqlparse(self._token.value[1:-1])[0],
            self.query.params
        )

    def to_mongo(self):
        pipeline = [
            {
                '$lookup': {
                    'from': self._in_query.left_table,
                    'pipeline': self._in_query._make_pipeline(),
                    'as': '_nested_in'
                }
            },
            {
                '$addFields': {
                    '_nested_in': {
                        '$map': {
                            'input': '$_nested_in',
                            'as': 'lookup_result',
                            'in': '$$lookup_result.' + self._in_query.selected_columns.sql_tokens[0].column
                        }
                    }
                }
            }
        ]
        return pipeline


class HavingConverter(Converter):
    nested_op: 'WhereOp' = None
    op: 'WhereOp' = None

    def __init__(self,
                 query: U['query_module.SelectQuery',
                          'query_module.BaseQuery'],
                 statement: SQLStatement):
        super().__init__(query, statement)

    def parse(self):
        tok = self.statement[:3]
        self.op = WhereOp(
            statement=tok,
            query=self.query,
            params=self.query.params
        )
        self.statement.skip(2)

    def to_mongo(self):
        return {'$match': self.op.to_mongo()}


class GroupbyConverter(Converter, _Tokens2Id):

    def __init__(self, *args):
        self.sql_tokens: List[SQLToken] = []
        super().__init__(*args)

    def parse(self):
        tok = self.statement.next()
        if not tok.match(tokens.Keyword, 'BY'):
            raise SQLDecodeError
        tok = self.statement.next()
        self.sql_tokens.extend(SQLToken.tokens2sql(tok, self.query))

    def to_mongo(self):
        _id = self.to_id()

        group = {
            '_id': _id
        }
        project = {
            '_id': False
        }
        for selected in self.query.selected_columns.sql_tokens:
            if isinstance(selected, SQLIdentifier):
                project[selected.field] = f'$_id.{selected.field}'
            else:
                project[selected.alias] = True
                group[selected.alias] = selected.to_mongo()

        pipeline = [
            {
                '$group': group
            },
            {
                '$project': project
            }
        ]

        return pipeline


class OffsetConverter(Converter):
    def __init__(self, *args):
        self.offset: int = None
        super().__init__(*args)

    def parse(self):
        tok = self.statement.next()
        self.offset = int(tok.value)

    def to_mongo(self):
        return {'skip': self.offset}


class AggOffsetConverter(OffsetConverter):

    def to_mongo(self):
        return {'$skip': self.offset}

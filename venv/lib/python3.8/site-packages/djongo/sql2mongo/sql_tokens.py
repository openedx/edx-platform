import abc
import re
from typing import Union as U, Iterator, Optional as O
from pymongo import ASCENDING, DESCENDING
from sqlparse import tokens, parse as sqlparse
from sqlparse.sql import Token, Identifier, Function, Comparison, Parenthesis, IdentifierList, Statement
from . import query as query_module
from ..exceptions import SQLDecodeError, NotSupportedError

all_token_types = U['SQLConstIdentifier',
                    'djongo.sql2mongo.functions.CountFunc',
                    'djongo.sql2mongo.functions.SimpleFunc',
                    'SQLIdentifier',
                    'SQLComparison',
                    'SQLPlaceholder']


class SQLToken:

    @abc.abstractmethod
    def __init__(self,
                 token: Token,
                 query: 'query_module.BaseQuery'):
        self._token = token
        self.query = query

    def __repr__(self):
        return f'{self._token}'

    @staticmethod
    def tokens2sql(token: Token,
                   query: 'query_module.BaseQuery'
                   ) -> Iterator[all_token_types]:
        from .functions import SQLFunc
        if isinstance(token, Identifier):
            # Bug fix for sql parse
            if isinstance(token[0], Parenthesis):
                try:
                    int(token[0][1].value)
                except ValueError:
                    yield SQLIdentifier(token[0][1], query)
                else:
                    yield SQLConstIdentifier(token, query)
            elif isinstance(token[0], Function):
                yield SQLFunc.token2sql(token, query)
            else:
                yield SQLIdentifier(token, query)
        elif isinstance(token, Function):
            yield SQLFunc.token2sql(token, query)
        elif isinstance(token, Comparison):
            yield SQLComparison(token, query)
        elif isinstance(token, IdentifierList):
            for tok in token.get_identifiers():
                yield from SQLToken.tokens2sql(tok, query)
        elif isinstance(token, Parenthesis):
            yield SQLPlaceholder(token, query)
        else:
            raise SQLDecodeError(f'Unsupported: {token.value}')

    @staticmethod
    def token2sql(token: Token,
                  query: 'query_module.BaseQuery'
                  ) -> all_token_types:
        return next(SQLToken.tokens2sql(token, query))

    @staticmethod
    def placeholder_index(token) -> int:
        return int(re.match(r'%\(([0-9]+)\)s', token.value, flags=re.IGNORECASE).group(1))


class AliasableToken(SQLToken):

    @abc.abstractmethod
    def __init__(self, *args):
        super().__init__(*args)
        self.token_alias: 'query_module.TokenAlias' = self.query.token_alias

        if self.alias:
            self.token_alias.alias2token[self.alias] = self
            self.token_alias.token2alias[self] = self.alias
            if self.is_explicit_alias():
                self.token_alias.aliased_names.add(self.alias)

    def __hash__(self):
        if self.is_explicit_alias():
            return hash(self._token[0].value)
        return hash(self._token.value)

    def __eq__(self, other):
        return hash(self) == hash(other)

    def is_explicit_alias(self):
        return len(self._token.tokens) == 5 and self._token[2].match(tokens.Keyword, 'AS')

    @property
    def alias(self) -> str:
        # bug fix sql parse
        if not self._token.get_ordering():
            return self._token.get_alias()


class SQLIdentifier(AliasableToken):

    def __init__(self, *args):
        super().__init__(*args)
        self._ord = None
        if self._token.get_ordering():
            # Bug fix for sql parse
            self._ord = self._token.get_ordering()
            self._token = self._token[0]

    @property
    def order(self):
        if self._ord is None:
            raise SQLDecodeError
        return ORDER_BY_MAP[self._ord]

    @property
    def field(self) -> str:
        if self.given_table in self.query.token_alias.aliased_names:
            return self.given_table

        if self.table == self.query.left_table:
            return self.column
        else:
            return f'{self.table}.{self.column}'

    @property
    def table(self) -> str:
        name = self.given_table
        alias2token = self.token_alias.alias2token
        try:
            return alias2token[name].table
        except KeyError:
            return name

    @property
    def given_table(self) -> str:
        name = self._token.get_parent_name()
        if name is None:
            name = self._token.get_real_name()

        if name is None:
            raise SQLDecodeError
        return name

    @property
    def column(self) -> str:
        name = self._token.get_real_name()
        if name is None:
            raise SQLDecodeError
        return name


class SQLConstIdentifier(AliasableToken):

    def __init__(self, *args):
        super().__init__(*args)

    @property
    def value(self) -> int:
        return int(self._token[0][1].value)

    def to_mongo(self) -> dict:
        return {'$literal': self.value}


class SQLComparison(SQLToken):

    @property
    def left_table(self):
        lhs = SQLIdentifier(self._token.left, self.query)
        return lhs.table

    @property
    def left_column(self):
        lhs = SQLIdentifier(self._token.left, self.query)
        return lhs.column

    @property
    def right_table(self):
        rhs = SQLIdentifier(self._token.right, self.query)
        return rhs.table

    @property
    def right_column(self):
        rhs = SQLIdentifier(self._token.right, self.query)
        return rhs.column

    @property
    def rhs_indexes(self):
        if not self._token.right.ttype == tokens.Name.Placeholder:
            if self._token.right.match(tokens.Keyword, 'NULL'):
                return None
            raise SQLDecodeError

        index = self.placeholder_index(self._token.right)
        return index


class SQLPlaceholder(SQLToken):
    def __iter__(self):
        tok = self._token[1:-1][0]
        if isinstance(tok, IdentifierList):
            for aid in tok.get_identifiers():
                yield self.get_value(aid)

        else:
            yield self.get_value(tok)

    def __init__(self, token: Token, query: 'query_module.BaseQuery'):
        super().__init__(token, query)

    def get_value(self, tok: Token):
        if tok.ttype == tokens.Name.Placeholder:
            return self.placeholder_index(tok)
        elif tok.match(tokens.Keyword, 'NULL'):
            return None
        elif tok.match(tokens.Keyword, 'DEFAULT'):
            return 'DEFAULT'
        else:
            raise SQLDecodeError


class SQLStatement:

    @property
    def current_token(self) -> Token:
        return self._statement[self._tok_id]

    def __init__(self, statement: U[Statement, Token]):
        self._statement = statement
        self._tok_id = 0
        self._gen_inst = self._generator()

    def __getattr__(self, item):
        return getattr(self._statement, item)

    def __iter__(self) -> Token:
        yield from self._gen_inst

    def __repr__(self):
        return str(self._statement)

    def __getitem__(self, item: slice):
        start = (item.start or 0) + self._tok_id
        stop = item.stop and self._tok_id + item.stop
        sql = ''.join(str(tok) for tok in self._statement[start:stop])
        sql = sqlparse(sql)[0]
        return SQLStatement(sql)

    def next(self) -> O[Token]:
        # self._tok_id, token = self._statement.token_next(self._tok_id)
        try:
            return next(self._gen_inst)
        except StopIteration:
            return None

    def skip(self, num):
        self._tok_id += num

    @property
    def prev_token(self) -> Token:
        return self._statement.token_prev(self._tok_id)[1]

    @property
    def next_token(self) -> Token:
        return self._statement.token_next(self._tok_id)[1]

    def _generator(self):
        token = self._statement[self._tok_id]
        while self._tok_id is not None:
            yield token
            self._tok_id, token = self._statement.token_next(self._tok_id)


class SQLColumnDef:

    not_null = object()
    unique = object()
    autoincrement = object()
    primarykey = object()
    null = object()
    _map = {
        'UNIQUE': unique,
        'AUTOINCREMENT': autoincrement,
        'PRIMARY KEY': primarykey,
        'NOT NULL': not_null,
        'NULL': null
    }
    supported_data_types = None

    def __init__(self,
                 name: str = None,
                 data_type: str = None,
                 col_constraints: set = None):
        self.name = name
        self.data_type = data_type
        self.col_constraints = col_constraints

    @staticmethod
    def _get_constraints(others: str):
        while others:
            try:
                name, others = others.split(' ', 1)
            except ValueError:
                name = others
                others = None
            try:
                yield SQLColumnDef._map[name]
            except KeyError:
                if others:
                    try:
                        part2, others = others.split(' ', 1)
                    except ValueError:
                        part2 = others
                        others = None

                    name = f'{name} {part2}'
                    try:
                        yield SQLColumnDef._map[name]
                    except KeyError:
                        raise SQLDecodeError(f'Unknown column constraint: {name}')
                else:
                    raise SQLDecodeError(f'Unknown column constraint: {name}')

    @staticmethod
    def sql2col_defs(sql: str):
        sql = sql[1:-1]
        while sql:
            if sql[0] == '"':
                try:
                    def_str, sql = sql.split(',', 1)
                except ValueError:
                    def_str = sql
                    sql = None
                else:
                    sql = sql.strip()
                yield SQLColumnDef.def_str2col_def(def_str)
            elif sql.startswith('CONSTRAINT'):
                # Temporary hack
                indexes = [None]
                i = 0
                for i, c in enumerate(sql):
                    if c == '(':
                        if indexes[0] is None:
                            indexes.pop()
                        indexes.append(i)
                    elif c == ')':
                        indexes.pop()
                    if not indexes:
                        break
                if len(sql[i:]) > 1:
                    sql = sql[i+3:]
                else:
                    sql = None
                yield SQLColumnConstraint()
            else:
                raise SQLDecodeError(f'Syntax Error: {sql}')

    @classmethod
    def def_str2col_def(cls, def_str: str):
        if not cls.supported_data_types:
            from djongo.base import DatabaseWrapper
            cls.supported_data_types = set(DatabaseWrapper.data_types.values())

        name, other = def_str[1:].split('"', 1)
        other = other.strip()

        data_type, constraint_sql = other.split(' ', 1)
        if data_type not in cls.supported_data_types:
            raise NotSupportedError(f'Data of type: {data_type}')

        col_constraints = set(SQLColumnDef._get_constraints(constraint_sql))
        return SQLColumnDef(name=name,
                            data_type=data_type,
                            col_constraints=col_constraints)

    @classmethod
    def statement2col_defs(cls, token: Token):
        from djongo.base import DatabaseWrapper
        supported_data_types = set(DatabaseWrapper.data_types.values())

        defs = token.value.strip('()').split(',')
        for col in defs:
            col = col.strip()
            name, other = col.split(' ', 1)
            if name == 'CONSTRAINT':
                yield SQLColumnConstraint()
            else:
                if col[0] != '"':
                    raise SQLDecodeError('Column identifier not quoted')
                name, other = col[1:].split('"', 1)
                other = other.strip()

                data_type, constraint_sql = other.split(' ', 1)
                if data_type not in supported_data_types:
                    raise NotSupportedError(f'Data of type: {data_type}')

                col_constraints = set(SQLColumnDef._get_constraints(constraint_sql))
                yield SQLColumnDef(name=name,
                                   data_type=data_type,
                                   col_constraints=col_constraints)


class SQLColumnConstraint(SQLColumnDef):
    pass


ORDER_BY_MAP = {
    'ASC': ASCENDING,
    'DESC': DESCENDING
}

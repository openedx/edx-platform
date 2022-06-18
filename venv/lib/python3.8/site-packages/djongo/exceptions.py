from dataclasses import dataclass
from typing import Sequence, Any

djongo_access_url = 'https://nesdis.github.io/djongo/support/'
_printed_features = set()


@dataclass(repr=False)
class SQLDecodeError(ValueError):
    err_key: Any = None
    err_sub_sql: Any = None
    err_sql: Any = None
    params: Sequence = None
    version: str = None

    def __repr__(self):
        return (f'\n\n\tKeyword: {self.err_key}\n'
                f'\tSub SQL: {self.err_sub_sql}\n'
                f'\tFAILED SQL: {self.err_sql}\n'
                f'\tParams: {self.params}\n'
                f'\tVersion: {self.version}')

    def __str__(self):
        return repr(self)


class NotSupportedError(ValueError):

    def __init__(self, keyword=None):
        self.keyword = keyword


class MigrationError(Exception):

    def __init__(self, field):
        self.field = field


def print_warn(feature=None, message=None):
    if feature not in _printed_features:
        message = ((message or f'This version of djongo does not support "{feature}" fully. ')
                   + f'Visit {djongo_access_url}')
        print(message)
        _printed_features.add(feature)
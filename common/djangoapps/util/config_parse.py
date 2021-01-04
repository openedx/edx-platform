"""
Helper functions for configuration parsing
"""


import collections

import six


def convert_tokens(tokens):
    """
    This function is called on the token
    dictionary that is imported from a yaml file.
    It returns a new dictionary where
    all strings containing 'None' are converted
    to a literal None due to a bug in Ansible
    """

    if tokens == 'None':
        return None
    elif isinstance(tokens, six.string_types) or (not isinstance(tokens, collections.Iterable)):
        return tokens
    elif isinstance(tokens, dict):
        return {
            convert_tokens(k): convert_tokens(v)
            for k, v in tokens.items()
        }
    else:
        return [convert_tokens(v) for v in tokens]

#!/usr/bin/env python3
"""
@@TODO
"""
from collections import defaultdict
import sys
import logging


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def run_dircheck(script_name, args):
    """
    @@TODO
    """
    if len(args) > 1:
        logger.critical("Invalid usage.\n%s", get_usage(script_name))
        return 123
    raise NotImplementedError()
    '''
    pylint_output_lines = get_pylint_output()
    pylint_issues_by_type = defaultdict(lambda: [])
    for line in pylint_output_lines:
        message_type, a, b, c, d = parse(line)
        pylint_issues_by_type[message_type.lower()].append(aggregate(a, b, c, d))
    # @@TODO
    '''


def get_usage(script_name):
    return (
        "Usage: {script_name} [DIRECTORY]\n"
        "Run directory-level checks for DIRECTORY and lower.\n"
        "Defaults to current working directory."
    ).format(script_name=script_name)


if __name__ == "__main__":
    sys.exit(run_dircheck(sys.argv[0], sys.argv[1:]))

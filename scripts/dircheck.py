#!/usr/bin/env python3
"""
@@TODO
"""
import logging
import os
import re
import sys
from collections import namedtuple
from pathlib import Path

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def run_dircheck(script_name, args):
    """
    @@TODO
    """
    if len(args) > 1:
        logger.critical("Invalid usage.\n%s", get_usage(script_name))
        return 123
    invoked_dir = Path.cwd()
    repo_root_dir = get_repo_root_dir(invoked_dir)
    target_dir = Path(args[0] if args else ".")
    issues_by_type = run_pylint(invoke_dir=repo_root_dir, target_dir=target_dir)
    print(issues_by_type)
    logger.critical("Warning: not fully implemented")
    return 0


def run_pylint(invoke_dir, target_dir):
    """
    Run pylint on `target_dir` from within `invoke_dir`.

    Side-effect: Changes working dir to `invoke_dir`.

    Returns: dict[str: list[PylintIssue]]
        Keys are uppercase chars indicating message type (C, R, W, E, F);
        values are lists of pylint issues for each.

    Example:
        run_pylint(
            Path('/home/bob/edx-platform'),
            Path('/home/bob/edx-platform/lms'),
        ) == {
            'C': [...], 'R': [...], 'W':[...]0, 'E':[...] 'F': [...]
        }
    """
    logger.info("Running pylint on '%s' from '%s'", target_dir, invoke_dir)
    issues_by_type = {'C': [], 'R': [], 'W': [], 'E': [], 'F': []}
    os.chdir(str(invoke_dir))
    command = 'pylint {target_dir}'.format(target_dir=target_dir)
    with os.popen(command) as pipe:
        for issue_string in pipe:
            issue = parse_pylint_issue(issue_string)
            if not issue:
                continue
            issues_by_type[issue.message_type].append(issue)
    return issues_by_type


PylintIssue = namedtuple(
    'PylintIssue',
    'path line_num column_num hint message_type message_num message_code message_text'
)

PYLINT_ISSUE_REGEX = re.compile(
    r"^(?P<path>.+?)"
    r":(?P<line_num>[0-9]+)"
    r":(?P<column_num>[0-9]+)"
    r": (?P<message_num>(?P<message_type>[CRWEF])\d+)"
    r": (?P<message_text>.+?)"
    r" \((?P<message_code>)\)",
    re.VERBOSE
)


def parse_pylint_issue(issue_string):
    """
    Parse a PylintIssue from a line of pylint output.

    Return None if line does not encode a Pylint issue in the expected format.

    Arguments:
        issue_string (str)

    Returns: PylintIssue|None
    """
    stripped = issue_string.strip()
    if not stripped:
        return None
    if stripped.startswith('***'):
        return None
    if stripped.startswith('---'):
        return None
    if stripped.startswith('Your code has'):
        return None
    match = PYLINT_ISSUE_REGEX.match(stripped)
    if match:
        return PylintIssue(**match.groupdict())
    logger.warning('Pylint output line not understood: %s', stripped)
    return None


def get_repo_root_dir(repo_sub_dir):
    """
    Get the root of a git repo given it or one its subdirectories.

    Assumes that we are within a git repo.
    If not, we will end up raising on OSError when we try to cd too high.

    Assumes that we are not in a git submodule
    (i.e., a subfolder of a repo that has a `.git` folder).

    Arguments:
        repo_sub_dir (Path)

    Returns: Path
    """
    if (repo_sub_dir / '.git').is_dir():
        return repo_sub_dir
    return get_repo_root_dir(repo_sub_dir.parent)


def get_usage(script_name):
    """
    @@TODO
    """
    return (
        "Usage: {script_name} [DIRECTORY]\n"
        "Run directory-level checks for DIRECTORY and lower.\n"
        "Defaults to current working directory."
    ).format(script_name=script_name)


if __name__ == "__main__":
    sys.exit(run_dircheck(sys.argv[0], sys.argv[1:]))

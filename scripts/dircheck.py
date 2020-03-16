#!/usr/bin/env python3
"""
@@TODO
"""
import json
import os
import pprint
import re
import sys
from collections import namedtuple
from pathlib import Path

CONFIG_FNAME = "dircheck.json"


def run_dircheck(script_name, args):
    """
    @@TODO
    """
    if len(args) > 1:
        output("Invalid usage.", status='error')
        output(get_usage(script_name), status='error')
        return 123
    target_dir = Path(args[0] if args else ".")
    repo_root_dir, config = get_repo_root_and_config(target_dir)
    issues_by_type = run_pylint(invoke_dir=repo_root_dir, target_dir=target_dir)
    output(config)
    output(issues_by_type)
    output("Warning: not fully implemented", status='warning')
    return 0


def get_repo_root_and_config(start_dir):
    """
    Find root of Git repository and load dircheck configuration.

    Start in `start_dir` and walk upwards until we reach root of repository,
    which is identified by the presence of a .git/ folder.
    If we find one dircheck.json, load it.
    If we find more than one dircheck.json, raise an Exception.
    If we find no dircheck.json, return None as dircheck dircheck_config.

    This function assumes that (1) `start_dir` is within a git repo
    and (2) there are no git submodules in this repository.

    Arguments:
        start_dir (Path)

    Returns: (repo_root: Path, dircheck_config: dict)
    """
    def walk_up(current_dir, dircheck_config):
        """
        @@TODO
        """
        if (current_dir / CONFIG_FNAME).is_file():
            if dircheck_config:
                error_message = (
                    "{current_dir} has {config_fname}, "
                    "but also contains subdirectory with {config_fname}."
                ).format(current_dir=current_dir, config_fname=CONFIG_FNAME)
                raise Exception(error_message)
            with open(str(current_dir / CONFIG_FNAME)) as dircheck_file:
                dircheck_config = json.load(dircheck_file)
        if (current_dir / '.git').is_dir():
            return current_dir, dircheck_config
        else:
            return walk_up(
                current_dir=current_dir.parent, dircheck_config=dircheck_config
            )
    return walk_up(current_dir=start_dir, dircheck_config=None)


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
            'I': [...], 'C': [...], 'R': [...], 'W':[...]0, 'E':[...] 'F': [...]
        }
    """
    output("Running pylint on '{target_dir}' from '{invoke_dir}'".format(
        target_dir=target_dir, invoke_dir=invoke_dir
    ))
    issues_by_type = {'I': [], 'C': [], 'R': [], 'W': [], 'E': [], 'F': []}
    os.chdir(str(invoke_dir))
    command = 'pylint {target_dir}'.format(target_dir=target_dir)
    with os.popen(command) as pipe:
        for issue_string in pipe:
            subcommand_output("pylint", issue_string)
            issue = parse_pylint_issue(issue_string)
            if not issue:
                continue
            issues_by_type[issue.message_type].append(issue)
    return issues_by_type


PylintIssue = namedtuple('PylintIssue', [
    'path',
    'line_num',
    'column_num',
    'message_type',
    'message_num',
    'message_symbol',
    'message',
    'full_text',
])

PYLINT_ISSUE_REGEX = re.compile(r"""
    ^(?P<path>.+?)
    :(?P<line_num>\d+)
    :(?P<column_num>\d+)
    :\ (?P<message_num>(?P<message_type>[CRWEF])\d\d\d\d)
    :\ (?P<message>.+?)
    \ \((?P<message_symbol>[a-z0-9-]+)\)$
""", re.VERBOSE)


INFO = "\033[1;34m"  # Bold blue
ERROR = "\033[1;31m"  # Bold red
WARNING = "\033[1;33m"  # Bold yellow
SUCCESS = "\033[1;32m"  # Bold green
NORMAL = "\033[0m"  # No styling


def output(message, status='info'):
    """
    Write a line of output, followed by a newline.
    """
    color = {
        'info': INFO, 'error': ERROR, 'warning': WARNING, 'success': SUCCESS
    }[status]
    to_output = "{color}{message}{NORMAL}".format(
        message=message, color=color, NORMAL=NORMAL
    )
    print(to_output)


def output_object(obj):
    """
    Output an object for debugging.
    """
    pprint.pprint(obj)


def subcommand_output(sub_command, message):
    """
    Write a line of output from one of the invoked sub-commands.

    Assumes newline is included in message.
    """
    to_output = "{INFO}({sub_command})>{NORMAL} {message}".format(
        sub_command=sub_command, message=message, INFO=INFO, NORMAL=NORMAL
    )
    print(to_output, end='')


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
    if stripped.startswith('Your code has been rated'):
        return None
    match = PYLINT_ISSUE_REGEX.match(stripped)
    if not match:
        output(
            'Pylint output line not understood: {stripped}'.format(
                stripped=stripped
            ),
            status='warning',
        )
        return None
    issue_dict = match.groupdict().copy()
    issue_dict['line_num'] = int(issue_dict['line_num'])
    issue_dict['column_num'] = int(issue_dict['column_num'])
    return PylintIssue(full_text=stripped, **issue_dict)


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

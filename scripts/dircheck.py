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
from enum import Enum
from pathlib import Path

CONFIG_FNAME = "dircheck.json"

INFO = "\033[1;34m"  # Bold blue
ERROR = "\033[1;31m"  # Bold red
WARNING = "\033[1;33m"  # Bold yellow
SUCCESS = "\033[1;32m"  # Bold green
NORMAL = "\033[0m"  # No styling


class CheckResult(Enum):
    """
    @@TODO
    """
    success = 'success'
    failure = 'failure'
    skipped = 'skipped'

    @property
    def is_success(self):
        return self == self.success

    @property
    def is_failure(self):
        return self == self.failure

    @property
    def is_skipped(self):
        return self == self.skipped


def main(script_name, args):
    """
    @@TODO
    """
    if len(args) > 1:
        output("Invalid usage.", status='error')
        output(get_usage(script_name), status='error')
        return 123
    target_dir = Path(args[0] if args else ".")
    repo_root_dir, dir_config = get_repo_root_and_config(target_dir)
    results_by_check = run_checks(
        check_classes=[PylintCheck],
        dir_config=dir_config,
        invoke_dir=repo_root_dir,
        target_dir=target_dir,
    )
    return report_results_and_get_exit_code(results_by_check)


def get_usage(script_name):
    """
    @@TODO
    """
    return (
        "Usage: {script_name} [DIRECTORY]\n"
        "Run directory-level checks for DIRECTORY and lower.\n"
        "Defaults to current working directory."
    ).format(script_name=script_name)


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


def run_checks(check_classes, dir_config, invoke_dir, target_dir, stop_on_failure=False):
    """
    @@TODO
    """
    results_by_check = {}
    for check_class in check_classes:
        key = check_class.check_key
        results_by_check[key] = CheckResult.skipped
        dir_config_for_check = dir_config.get(key)
        check = check_class(
            config=dir_config_for_check,
            invoke_dir=invoke_dir,
            target_dir=target_dir,
        )
        if not check.enabled:
            continue
        result = CheckResult.success if check.run() else CheckResult.failure
        results_by_check[key] = result
        if stop_on_failure and result.is_failure:
            return
    return results_by_check


def report_results_and_get_exit_code(results_by_check):
    """
    @@TODO
    """
    successful_checks = [c for c, r in results_by_check.items() if r.is_success]
    skipped_checks = [c for c, r in results_by_check.items() if r.is_skipped]
    failed_checks = [c for c, r in results_by_check.items() if r.is_failure]
    if skipped_checks:
        output(
            "Checks not run: {}.".format(skipped_checks.join(", ")),
            status="warning",
        )
    if successful_checks:
        output(
            "Successful checks: {}.".format(successful_checks.join(", ")),
            status="ok",
        )
    if failed_checks:
        output(
            "Failed checks: {}.".format(failed_checks.join(", ")),
            status="error",
        )
    if successful_checks and not failed_checks:
        return 0
    elif failed_checks:
        return 1
    else:
        output(
            "Failing because no checks were run.",
            status="error",
        )
        return 2


def output(message, status='info'):
    """
    Write a line of output, followed by a newline.
    """
    color = {
        'info': INFO, 'error': ERROR, 'warning': WARNING, 'ok': SUCCESS
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


class Check:
    """
    @@TODO
    """
    check_key = 'CHECK_KEY_NOT_SET'

    def __init__(self, dir_config, invoke_dir, target_dir):
        """
        @TODO
        """
        self.dir_config = dir_config
        self.invoke_dir = invoke_dir
        self.target_dir = target_dir

    def run(self):
        """
        @@TODO
        """
        return NotImplementedError

    @property
    def enabled(self):
        """
        @@TODO
        """
        return NotImplementedError

    @classmethod
    def subcommand_output(cls, message):
        """
        Write a line of output coming from a check's output.

        Assumes newline is included in message.
        """
        to_output = "{INFO}({check_key})>{NORMAL} {message}".format(
            check_key=cls.check_key, message=message, INFO=INFO, NORMAL=NORMAL
        )
        print(to_output, end='')


class PylintCheck(Check):
    """
    @@TODO
    """
    check_key = "pylint"

    def run(self):
        """
        @@TODO
        """
        return CheckResult.failure

    @property
    def enabled(self):
        """
        @@TODO
        """
        return self.dir_config is not None

    def _run_pylint(self, invoke_dir, target_dir):
        """
        Run pylint on `target_dir` from within `invoke_dir`.

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
        original_dir = Path.cwd()
        os.chdir(str(invoke_dir))
        issues_by_type = {'I': [], 'C': [], 'R': [], 'W': [], 'E': [], 'F': []}
        command = 'pylint {target_dir}'.format(target_dir=target_dir)
        with os.popen(command) as pipe:
            for issue_string in pipe:
                self.subcommand_output(issue_string)
                issue = self._parse_pylint_issue(issue_string)
                if not issue:
                    continue
                issues_by_type[issue.message_type].append(issue)
        os.chdir(str(original_dir))
        return issues_by_type

    PYLINT_ISSUE_REGEX = re.compile(r"""
        ^(?P<path>.+?)
        :(?P<line_num>\d+)
        :(?P<column_num>\d+)
        :\ (?P<message_num>(?P<message_type>[CRWEF])\d\d\d\d)
        :\ (?P<message>.+?)
        \ \((?P<message_symbol>[a-z0-9-]+)\)$
    """, re.VERBOSE)

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

    def _parse_pylint_issue(self, issue_string):
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
        match = self.PYLINT_ISSUE_REGEX.match(stripped)
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
        return self.PylintIssue(full_text=stripped, **issue_dict)


if __name__ == "__main__":
    sys.exit(main(sys.argv[0], sys.argv[1:]))

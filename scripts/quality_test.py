"""  # lint-amnesty, pylint: disable=django-not-configured
Check code quality using pycodestyle, pylint, and diff_quality.
"""

import argparse
import glob
import json
import os
import re
import sys
import subprocess
import shutil
from pathlib import Path
from time import sleep

try:
    from pygments.console import colorize
except ImportError:
    colorize = lambda color, text: text


class BuildFailure(Exception):
    """Represents a problem with some part of the build's execution."""


def fail_quality(name, message):
    """
    Fail the specified quality check.
    """
    print(name)
    print(message)
    sys.exit()


def _prepare_report_dir(dir_name):
    """
    Sets a given directory to a created, but empty state
    """
    if os.path.isdir(dir_name):
        shutil.rmtree(dir_name)
    os.makedirs(dir_name, exist_ok=True)


def repo_root():
    """
    Get the root of the git repository (edx-platform).

    This sometimes fails on Docker Devstack, so it's been broken
    down with some additional error handling.  It usually starts
    working within 30 seconds or so; for more details, see
    https://openedx.atlassian.net/browse/PLAT-1629 and
    https://github.com/docker/for-mac/issues/1509
    """

    file_path = Path(__file__)
    max_attempts = 180
    for attempt in range(1, max_attempts + 1):
        try:
            absolute_path = file_path.resolve(strict=True)
            return absolute_path.parents[1]
        except OSError:
            print(f'Attempt {attempt}/{max_attempts} to get an absolute path failed')
            if attempt < max_attempts:
                sleep(1)
            else:
                print('Unable to determine the absolute path of the edx-platform repo, aborting')
                raise RuntimeError('Could not determine the repository root after multiple attempts')


def _get_report_contents(filename, report_name, last_line_only=False):
    """
    Returns the contents of the given file. Use last_line_only to only return
    the last line, which can be used for getting output from quality output
    files.

    Arguments:
        last_line_only: True to return the last line only, False to return a
            string with full contents.

    Returns:
        String containing full contents of the report, or the last line.

    """
    if os.path.isfile(filename):
        with open(filename) as report_file:
            if last_line_only:
                lines = report_file.readlines()
                for line in reversed(lines):
                    if line != '\n':
                        return line
                return None
            else:
                return report_file.read()
    else:
        file_not_found_message = f"FAILURE: The following log file could not be found: {filename}"
        fail_quality(report_name, file_not_found_message)


def _get_count_from_last_line(filename, file_type):
    """
    This will return the number in the last line of a file.
    It is returning only the value (as a floating number).
    """
    report_contents = _get_report_contents(filename, file_type, last_line_only=True)
    if report_contents is None:
        return 0

    last_line = report_contents.strip()
    # Example of the last line of a compact-formatted eslint report (for example): "62829 problems"
    regex = r'^\d+'

    try:
        return float(re.search(regex, last_line).group(0))
    # An AttributeError will occur if the regex finds no matches.
    # A ValueError will occur if the returned regex cannot be cast as a float.
    except (AttributeError, ValueError):
        return None


def _get_stylelint_violations():
    """
    Returns the number of Stylelint violations.
    """
    REPO_ROOT = repo_root()
    REPORT_DIR = REPO_ROOT / 'reports'
    stylelint_report_dir = (REPORT_DIR / "stylelint")
    stylelint_report = stylelint_report_dir / "stylelint.report"
    _prepare_report_dir(stylelint_report_dir)

    command = [
        'node', 'node_modules/stylelint',
        '*scss_files',
        '--custom-formatter', 'stylelint-formatter-pretty/index.js'
    ]

    with open(stylelint_report, 'w') as report_file:
        subprocess.run(
            command,
            check=True,
            stdout=report_file,
            stderr=subprocess.STDOUT,
            text=True
        )

    try:
        return int(_get_count_from_last_line(stylelint_report, "stylelint"))
    except TypeError:
        fail_quality(
            'stylelint',
            "FAILURE: Number of stylelint violations could not be found in {stylelint_report}".format(
                stylelint_report=stylelint_report
            )
        )


def run_eslint():
    """
    Runs eslint on static asset directories.
    If limit option is passed, fails build if more violations than the limit are found.
    """

    REPO_ROOT = repo_root()
    REPORT_DIR = REPO_ROOT / 'reports'
    eslint_report_dir = REPORT_DIR / "eslint"
    eslint_report = eslint_report_dir / "eslint.report"
    _prepare_report_dir(eslint_report_dir)
    violations_limit = 4950

    command = [
        "node",
        "--max_old_space_size=4096",
        "node_modules/.bin/eslint",
        "--ext", ".js",
        "--ext", ".jsx",
        "--format=compact",
        "."
    ]

    with open(eslint_report, 'w') as report_file:
        subprocess.run(
            command,
            stdout=report_file,
            stderr=subprocess.STDOUT,
            text=True,
            check=False
        )

    try:
        num_violations = int(_get_count_from_last_line(eslint_report, "eslint"))
    except TypeError:
        fail_quality(
            'eslint',
            "FAILURE: Number of eslint violations could not be found in {eslint_report}".format(
                eslint_report=eslint_report
            )
        )

    # Fail if number of violations is greater than the limit
    if num_violations > violations_limit > -1:
        fail_quality(
            'eslint',
            "FAILURE: Too many eslint violations ({count}).\nThe limit is {violations_limit}.".format(
                count=num_violations, violations_limit=violations_limit
            )
        )
    else:
        print("successfully run eslint with violations")
        print(num_violations)


def run_stylelint():
    """
    Runs stylelint on Sass files.
    If limit option is passed, fails build if more violations than the limit are found.
    """

    violations_limit = 0
    num_violations = _get_stylelint_violations()
    # Fail if number of violations is greater than the limit
    if num_violations > violations_limit:
        fail_quality(
            'stylelint',
            "FAILURE: Stylelint failed with too many violations: ({count}).\nThe limit is {violations_limit}.".format(
                count=num_violations,
                violations_limit=violations_limit,
            )
        )
    else:
        print("successfully run stylelint with violations")
        print(num_violations)


def _extract_missing_pii_annotations(filename):
    """
    Returns the number of uncovered models from the stdout report of django_find_annotations.

    Arguments:
        filename: Filename where stdout of django_find_annotations was captured.

    Returns:
        three-tuple containing:
            1. The number of uncovered models,
            2. A bool indicating whether the coverage is still below the threshold, and
            3. The full report as a string.
    """
    uncovered_models = 0
    pii_check_passed = True
    if os.path.isfile(filename):
        with open(filename) as report_file:
            lines = report_file.readlines()

            # Find the count of uncovered models.
            uncovered_regex = re.compile(r'^Coverage found ([\d]+) uncovered')
            for line in lines:
                uncovered_match = uncovered_regex.match(line)
                if uncovered_match:
                    uncovered_models = int(uncovered_match.groups()[0])
                    break

            # Find a message which suggests the check failed.
            failure_regex = re.compile(r'^Coverage threshold not met!')
            for line in lines:
                failure_match = failure_regex.match(line)
                if failure_match:
                    pii_check_passed = False
                    break

            # Each line in lines already contains a newline.
            full_log = ''.join(lines)
    else:
        fail_quality('pii', f'FAILURE: Log file could not be found: {filename}')

    return (uncovered_models, pii_check_passed, full_log)


def run_pii_check():
    """
    Guarantee that all Django models are PII-annotated.
    """
    REPO_ROOT = repo_root()
    REPORT_DIR = REPO_ROOT / 'reports'
    pii_report_name = 'pii'
    default_report_dir = (REPORT_DIR / pii_report_name)
    report_dir = default_report_dir
    output_file = os.path.join(report_dir, 'pii_check_{}.report')
    env_report = []
    pii_check_passed = True

    for env_name, env_settings_file in (("CMS", "cms.envs.test"), ("LMS", "lms.envs.test")):
        try:
            print(f"Running {env_name} PII Annotation check and report")
            print("-" * 45)

            run_output_file = str(output_file).format(env_name.lower())
            os.makedirs(report_dir, exist_ok=True)

            # Prepare the environment for the command
            env = {
                **os.environ,  # Include the current environment variables
                "DJANGO_SETTINGS_MODULE": env_settings_file  # Set DJANGO_SETTINGS_MODULE for each environment
            }

            command = [
                "code_annotations",
                "django_find_annotations",
                "--config_file", ".pii_annotations.yml",
                "--report_path", str(report_dir),
                "--app_name", env_name.lower()
            ]

            # Run the command without shell=True
            with open(run_output_file, 'w') as report_file:
                subprocess.run(
                    command,
                    env=env,  # Pass the environment with DJANGO_SETTINGS_MODULE
                    check=True,
                    stdout=report_file,
                    stderr=subprocess.STDOUT,
                    text=True
                )

            # Extract results
            uncovered_model_count, pii_check_passed_env, full_log = _extract_missing_pii_annotations(run_output_file)
            env_report.append((
                uncovered_model_count,
                full_log,
            ))

        except BuildFailure as error_message:
            fail_quality(pii_report_name, f'FAILURE: {error_message}')

        # Update pii_check_passed based on the result of the current environment
        if not pii_check_passed_env:
            pii_check_passed = False

    # If the PII check failed in any environment, fail the task
    if not pii_check_passed:
        fail_quality('pii', full_log)
    else:
        print("Successfully ran pii_check")


def check_keywords():
    """
    Check Django model fields for names that conflict with a list of reserved keywords
    """
    REPO_ROOT = repo_root()
    REPORT_DIR = REPO_ROOT / 'reports'
    report_path = REPORT_DIR / 'reserved_keywords'
    report_path.mkdir(parents=True, exist_ok=True)

    overall_status = True
    for env_name, env_settings_file in [('lms', 'lms.envs.test'), ('cms', 'cms.envs.test')]:
        report_file_path = report_path / f"{env_name}_reserved_keyword_report.csv"
        override_file = os.path.join(REPO_ROOT, "db_keyword_overrides.yml")
        try:
            env = {
                **os.environ,  # Include the current environment variables
                "DJANGO_SETTINGS_MODULE": env_settings_file  # Set DJANGO_SETTINGS_MODULE for each environment
            }
            command = [
                "python", "manage.py", env_name, "check_reserved_keywords",
                "--override_file", str(override_file),
                "--report_path", str(report_path),
                "--report_file", str(report_file_path)
            ]
            with open(report_file_path, 'w') as report_file:
                subprocess.run(
                    command,
                    env=env,
                    check=True,
                    stdout=report_file,
                    stderr=subprocess.STDOUT,
                    text=True
                )
        except BuildFailure:
            overall_status = False
    if not overall_status:
        fail_quality(
            'keywords',
            'Failure: reserved keyword checker failed. Reports can be found here: {}'.format(
                report_path
            )
        )
    else:
        print("successfully run check_keywords")


def _get_xsslint_counts(filename):
    """
    This returns a dict of violations from the xsslint report.

    Arguments:
        filename: The name of the xsslint report.

    Returns:
        A dict containing the following:
            rules: A dict containing the count for each rule as follows:
                violation-rule-id: N, where N is the number of violations
            total: M, where M is the number of total violations

    """
    report_contents = _get_report_contents(filename, 'xsslint')
    rule_count_regex = re.compile(r"^(?P<rule_id>[a-z-]+):\s+(?P<count>\d+) violations", re.MULTILINE)
    total_count_regex = re.compile(r"^(?P<count>\d+) violations total", re.MULTILINE)
    violations = {'rules': {}}
    for violation_match in rule_count_regex.finditer(report_contents):
        try:
            violations['rules'][violation_match.group('rule_id')] = int(violation_match.group('count'))
        except ValueError:
            violations['rules'][violation_match.group('rule_id')] = None
    try:
        violations['total'] = int(total_count_regex.search(report_contents).group('count'))
    # An AttributeError will occur if the regex finds no matches.
    # A ValueError will occur if the returned regex cannot be cast as a float.
    except (AttributeError, ValueError):
        violations['total'] = None
    return violations


def run_xsslint():
    """
    Runs xsslint/xss_linter.py on the codebase
    """

    try:
        thresholds_option = 'scripts/xsslint_thresholds.json'
        # Read the JSON file
        with open(thresholds_option, 'r') as file:
            violation_thresholds = json.load(file)

    except ValueError:
        violation_thresholds = None
    if isinstance(violation_thresholds, dict) is False or \
            any(key not in ("total", "rules") for key in violation_thresholds.keys()):

        fail_quality(
            'xsslint',
            """FAILURE: Thresholds option "{thresholds_option}" was not supplied using proper format.\n"""
            """Here is a properly formatted example, '{{"total":100,"rules":{{"javascript-escape":0}}}}' """
            """with property names in double-quotes.""".format(
                thresholds_option=thresholds_option
            )
        )

    xsslint_script = "xss_linter.py"
    REPO_ROOT = repo_root()
    REPORT_DIR = REPO_ROOT / 'reports'
    xsslint_report_dir = (REPORT_DIR / "xsslint")
    xsslint_report = xsslint_report_dir / "xsslint.report"
    _prepare_report_dir(xsslint_report_dir)

    command = [
        f"{REPO_ROOT}/scripts/xsslint/{xsslint_script}",
        "--rule-totals",
        "--config=scripts.xsslint_config"
    ]
    with open(xsslint_report, 'w') as report_file:
        subprocess.run(
            command,
            check=True,
            stdout=report_file,
            stderr=subprocess.STDOUT,
            text=True
        )
    xsslint_counts = _get_xsslint_counts(xsslint_report)

    try:
        metrics_str = "Number of {xsslint_script} violations: {num_violations}\n".format(
            xsslint_script=xsslint_script, num_violations=int(xsslint_counts['total'])
        )
        if 'rules' in xsslint_counts and any(xsslint_counts['rules']):
            metrics_str += "\n"
            rule_keys = sorted(xsslint_counts['rules'].keys())
            for rule in rule_keys:
                metrics_str += "{rule} violations: {count}\n".format(
                    rule=rule,
                    count=int(xsslint_counts['rules'][rule])
                )
    except TypeError:
        fail_quality(
            'xsslint',
            "FAILURE: Number of {xsslint_script} violations could not be found in {xsslint_report}".format(
                xsslint_script=xsslint_script, xsslint_report=xsslint_report
            )
        )

    error_message = ""
    # Test total violations against threshold.
    if 'total' in list(violation_thresholds.keys()):
        if violation_thresholds['total'] < xsslint_counts['total']:
            error_message = "Too many violations total ({count}).\nThe limit is {violations_limit}.".format(
                count=xsslint_counts['total'], violations_limit=violation_thresholds['total']
            )

    # Test rule violations against thresholds.
    if 'rules' in violation_thresholds:
        threshold_keys = sorted(violation_thresholds['rules'].keys())
        for threshold_key in threshold_keys:
            if threshold_key not in xsslint_counts['rules']:
                error_message += (
                    "\nNumber of {xsslint_script} violations for {rule} could not be found in "
                    "{xsslint_report}."
                ).format(
                    xsslint_script=xsslint_script, rule=threshold_key, xsslint_report=xsslint_report
                )
            elif violation_thresholds['rules'][threshold_key] < xsslint_counts['rules'][threshold_key]:
                error_message += \
                    "\nToo many {rule} violations ({count}).\nThe {rule} limit is {violations_limit}.".format(
                        rule=threshold_key, count=xsslint_counts['rules'][threshold_key],
                        violations_limit=violation_thresholds['rules'][threshold_key],
                    )

    if error_message:
        fail_quality(
            'xsslint',
            "FAILURE: XSSLinter Failed.\n{error_message}\n"
            "See {xsslint_report} or run the following command to hone in on the problem:\n"
            "  ./scripts/xss-commit-linter.sh -h".format(
                error_message=error_message, xsslint_report=xsslint_report
            )
        )
    else:
        print("successfully run xsslint")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=['eslint', 'stylelint',
                                            'xsslint', 'pii_check', 'check_keywords'])

    argument = parser.parse_args()

    if argument.command == 'eslint':
        run_eslint()

    elif argument.command == 'stylelint':
        run_stylelint()

    elif argument.command == 'xsslint':
        run_xsslint()

    elif argument.command == 'pii_check':
        run_pii_check()

    elif argument.command == 'check_keywords':
        check_keywords()

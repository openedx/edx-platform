# run_quality_checks.py

import os
import re
import subprocess

from pavelib.utils.envs import Env
from datetime import datetime
from xml.sax.saxutils import quoteattr

JUNIT_XML_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="{name}" tests="1" errors="0" failures="{failure_count}" skip="0">
<testcase classname="pavelib.quality" name="{name}" time="{seconds}">{failure_element}</testcase>
</testsuite>
"""
JUNIT_XML_FAILURE_TEMPLATE = '<failure message={message}/>'
START_TIME = datetime.utcnow()


def write_junit_xml(name, message=None):
    """
    Write a JUnit results XML file describing the outcome of a quality check.
    """
    if message:
        failure_element = JUNIT_XML_FAILURE_TEMPLATE.format(message=quoteattr(message))
    else:
        failure_element = ''
    data = {
        'failure_count': 1 if message else 0,
        'failure_element': failure_element,
        'name': name,
        'seconds': (datetime.utcnow() - START_TIME).total_seconds(),
    }
    Env.QUALITY_DIR.makedirs_p()
    filename = Env.QUALITY_DIR / f'{name}.xml'
    with open(filename, 'w') as f:
        f.write(JUNIT_XML_TEMPLATE.format(**data))


def fail_quality(name, message):
    """
    Fail the specified quality check by generating the JUnit XML results file
    and raising a ``BuildFailure``.
    """
    write_junit_xml(name, message)
    exit(1)


def _get_pep8_violations(clean=True):
    """
    Runs pycodestyle. Returns a tuple of (number_of_violations, violations_string)
    where violations_string is a string of all PEP 8 violations found, separated
    by new lines.
    """
    report_dir = (Env.REPORT_DIR / 'pep8')
    if clean:
        report_dir.rmtree(ignore_errors=True)
    report_dir.makedirs_p()
    report = report_dir / 'pep8.report'

    # Make sure the metrics subdirectory exists
    Env.METRICS_DIR.makedirs_p()

    if not report.exists():
        # sh(f'pycodestyle . | tee {report} -a')
        with open(report, 'w') as f:
            result = subprocess.run(['pycodestyle', '.'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            f.write(result.stdout.decode())

    violations_list = _pep8_violations(report)

    return len(violations_list), violations_list


def _pep8_violations(report_file):
    """
    Returns the list of all PEP 8 violations in the given report_file.
    """
    with open(report_file) as f:
        return f.readlines()


def run_pep8():  # pylint: disable=unused-argument
    """
    Run pycodestyle on system code.
    Fail the task if any violations are found.
    """
    (count, violations_list) = _get_pep8_violations()
    violations_list = ''.join(violations_list)

    # Print number of violations to log
    violations_count_str = f"Number of PEP 8 violations: {count}"
    print(violations_count_str)
    print(violations_list)

    # Also write the number of violations to a file
    with open(Env.METRICS_DIR / "pep8", "w") as f:
        f.write(violations_count_str + '\n\n')
        f.write(violations_list)

    # Fail if any violations are found
    if count:
        failure_string = "FAILURE: Too many PEP 8 violations. " + violations_count_str
        failure_string += f"\n\nViolations:\n{violations_list}"
        fail_quality('pep8', failure_string)
    else:
        write_junit_xml('pep8')


def _prepare_report_dir(dir_name):
    """
    Sets a given directory to a created, but empty state
    """
    dir_name.rmtree_p()
    dir_name.mkdir_p()


def _write_metric(metric, filename):
    """
    Write a given metric to a given file
    Used for things like reports/metrics/eslint, which will simply tell you the number of
    eslint violations found
    """
    Env.METRICS_DIR.makedirs_p()

    with open(filename, "w") as metric_file:
        metric_file.write(str(metric))


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
    stylelint_report_dir = (Env.REPORT_DIR / "stylelint")
    stylelint_report = stylelint_report_dir / "stylelint.report"
    _prepare_report_dir(stylelint_report_dir)
    formatter = 'node_modules/stylelint-formatter-pretty'

    # sh(
    #     "stylelint **/*.scss --custom-formatter={formatter} | tee {stylelint_report}".format(
    #         formatter=formatter,
    #         stylelint_report=stylelint_report,
    #     ),
    #     ignore_error=True
    # )

    command = f"stylelint **/*.scss --custom-formatter={formatter}"
    with open(stylelint_report, 'w') as report_file:
        result = subprocess.run(command, shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        report_file.write(result.stdout)

    if result.returncode != 0:
        print(f"Warning: stylelint command exited with non-zero status {result.returncode}")

    try:
        return int(_get_count_from_last_line(stylelint_report, "stylelint"))
    except TypeError:
        fail_quality(
            'stylelint',
            "FAILURE: Number of stylelint violations could not be found in {stylelint_report}".format(
                stylelint_report=stylelint_report
            )
        )


def run_stylelint():
    """
    Runs stylelint on Sass files.
    If limit option is passed, fails build if more violations than the limit are found.
    """
    violations_limit = 0
    num_violations = _get_stylelint_violations()

    # Record the metric
    _write_metric(num_violations, (Env.METRICS_DIR / "stylelint"))

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
        write_junit_xml('stylelint')


if __name__ == "__main__":
    run_pep8()
    run_stylelint()

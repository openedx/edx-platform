# run_quality_checks.py

import os
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


if __name__ == "__main__":
    run_pep8()

"""
Check code quality using pep8, pylint, and diff_quality.
"""
from paver.easy import sh, task, cmdopts, needs
import os
import errno
import re
from optparse import make_option

from .utils.envs import Env


@task
@needs('pavelib.prereqs.install_python_prereqs')
@cmdopts([
    ("system=", "s", "System to act on"),
    ("errors", "e", "Check for errors only"),
    ("limit=", "l", "limit for number of acceptable violations"),
])
def run_pylint(options):
    """
    Run pylint on system code. When violations limit is passed in,
    fail the task if too many violations are found.
    """
    num_violations = 0
    violations_limit = int(getattr(options, 'limit', -1))
    errors = getattr(options, 'errors', False)
    systems = getattr(options, 'system', 'lms,cms,common').split(',')

    for system in systems:
        # Directory to put the pylint report in.
        # This makes the folder if it doesn't already exist.
        report_dir = (Env.REPORT_DIR / system).makedirs_p()

        flags = '-E' if errors else ''

        apps = [system]

        for directory in ['djangoapps', 'lib']:
            dirs = os.listdir(os.path.join(system, directory))
            apps.extend([d for d in dirs if os.path.isdir(os.path.join(system, directory, d))])

        apps_list = ' '.join(apps)

        pythonpath_prefix = (
            "PYTHONPATH={system}:{system}/djangoapps:{system}/"
            "lib:common/djangoapps:common/lib".format(
                system=system
            )
        )

        sh(
            "{pythonpath_prefix} pylint {flags} -f parseable {apps} | "
            "tee {report_dir}/pylint.report".format(
                pythonpath_prefix=pythonpath_prefix,
                flags=flags,
                apps=apps_list,
                report_dir=report_dir
            )
        )

        num_violations += _count_pylint_violations(
            "{report_dir}/pylint.report".format(report_dir=report_dir))

    print("Number of pylint violations: " + str(num_violations))
    if num_violations > violations_limit > -1:
        raise Exception("Failed. Too many pylint violations. "
                        "The limit is {violations_limit}.".format(violations_limit=violations_limit))

def _count_pylint_violations(report_file):
    """
    Parses a pylint report line-by-line and determines the number of violations reported
    """
    num_violations_report = 0
    # An example string:
    # common/lib/xmodule/xmodule/tests/test_conditional.py:21: [C0111(missing-docstring), DummySystem] Missing docstring
    # More examples can be found in the unit tests for this method
    pylint_pattern = re.compile(".(\d+):\ \[(\D\d+.+\]).")

    for line in open(report_file):
        violation_list_for_line = pylint_pattern.split(line)
        # If the string is parsed into four parts, then we've found a violation. Example of split parts:
        # test file, line number, violation name, violation details
        if len(violation_list_for_line) == 4:
            num_violations_report += 1
    return num_violations_report

@task
@needs('pavelib.prereqs.install_python_prereqs')
@cmdopts([
    ("system=", "s", "System to act on"),
    ("limit=", "l", "limit for number of acceptable violations"),
])
def run_pep8(options):
    """
    Run pep8 on system code. When violations limit is passed in,
    fail the task if too many violations are found.
    """
    num_violations = 0
    systems = getattr(options, 'system', 'lms,cms,common').split(',')
    violations_limit = int(getattr(options, 'limit', -1))

    for system in systems:
        # Directory to put the pep8 report in.
        # This makes the folder if it doesn't already exist.
        report_dir = (Env.REPORT_DIR / system).makedirs_p()

        sh('pep8 {system} | tee {report_dir}/pep8.report'.format(system=system, report_dir=report_dir))
        num_violations = num_violations + _count_pep8_violations(
            "{report_dir}/pep8.report".format(report_dir=report_dir))

    print("Number of pep8 violations: " + str(num_violations))
    # Fail the task if the violations limit has been reached
    if num_violations > violations_limit > -1:
        raise Exception("Failed. Too many pep8 violations. "
                        "The limit is {violations_limit}.".format(violations_limit=violations_limit))

def _count_pep8_violations(report_file):
    num_lines = sum(1 for line in open(report_file))
    return num_lines

@task
@needs('pavelib.prereqs.install_python_prereqs')
def run_quality():
    """
    Build the html diff quality reports, and print the reports to the console.
    """

    # Directory to put the diff reports in.
    # This makes the folder if it doesn't already exist.
    dquality_dir = (Env.REPORT_DIR / "diff_quality").makedirs_p()

    # Generage diff-quality html report for pep8, and print to console
    # If pep8 reports exist, use those
    # Otherwise, `diff-quality` will call pep8 itself

    pep8_files = []
    for subdir, _dirs, files in os.walk(os.path.join(Env.REPORT_DIR)):
        for f in files:
            if f == "pep8.report":
                pep8_files.append(os.path.join(subdir, f))

    pep8_reports = u' '.join(pep8_files)

    sh(
        "diff-quality --violations=pep8 --html-report {dquality_dir}/"
        "diff_quality_pep8.html {pep8_reports}".format(
            dquality_dir=dquality_dir, pep8_reports=pep8_reports)
    )

    sh(
        "diff-quality --violations=pep8 {pep8_reports}".format(
            pep8_reports=pep8_reports)
    )

    # Generage diff-quality html report for pylint, and print to console
    # If pylint reports exist, use those
    # Otherwise, `diff-quality` will call pylint itself

    pylint_files = []
    for subdir, _dirs, files in os.walk(os.path.join(Env.REPORT_DIR)):
        for f in files:
            if f == "pylint.report":
                pylint_files.append(os.path.join(subdir, f))

    pylint_reports = u' '.join(pylint_files)

    pythonpath_prefix = (
        "PYTHONPATH=$PYTHONPATH:lms:lms/djangoapps:lms/lib:cms:cms/djangoapps:cms/lib:"
        "common:common/djangoapps:common/lib"
    )

    sh(
        "{pythonpath_prefix} diff-quality --violations=pylint --html-report "
        "{dquality_dir}/diff_quality_pylint.html {pylint_reports}".format(
            pythonpath_prefix=pythonpath_prefix,
            dquality_dir=dquality_dir,
            pylint_reports=pylint_reports
        )
    )

    sh(
        "{pythonpath_prefix} diff-quality --violations=pylint {pylint_reports}".format(
            pythonpath_prefix=pythonpath_prefix,
            pylint_reports=pylint_reports
        )
    )

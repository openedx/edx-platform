"""
Check code quality using pep8, pylint, and diff_quality.
"""
from paver.easy import sh, task, cmdopts, needs, BuildFailure
import os
import re

from .utils.envs import Env


@task
@needs('pavelib.prereqs.install_python_prereqs')
@cmdopts([
    ("system=", "s", "System to act on"),
])
def find_fixme(options):
    """
    Run pylint on system code, only looking for fixme items.
    """
    num_fixme = 0
    systems = getattr(options, 'system', 'lms,cms,common').split(',')

    for system in systems:
        # Directory to put the pylint report in.
        # This makes the folder if it doesn't already exist.
        report_dir = (Env.REPORT_DIR / system).makedirs_p()

        apps = [system]

        for directory in ['djangoapps', 'lib']:
            dirs = os.listdir(os.path.join(system, directory))
            apps.extend([d for d in dirs if os.path.isdir(os.path.join(system, directory, d))])

        apps_list = ' '.join(apps)

        pythonpath_prefix = (
            "PYTHONPATH={system}:{system}/lib"
            "common/djangoapps:common/lib".format(
                system=system
            )
        )

        sh(
            "{pythonpath_prefix} pylint --disable R,C,W,E --enable=fixme "
            "--msg-template={msg_template} {apps} "
            "| tee {report_dir}/pylint_fixme.report".format(
                pythonpath_prefix=pythonpath_prefix,
                msg_template='"{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}"',
                apps=apps_list,
                report_dir=report_dir
            )
        )

        num_fixme += _count_pylint_violations(
            "{report_dir}/pylint_fixme.report".format(report_dir=report_dir))

    print("Number of pylint fixmes: " + str(num_fixme))


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

        flags = []
        if errors:
            flags.append("--errors-only")

        apps = [system]

        for directory in ['lib']:
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
            "{pythonpath_prefix} pylint {flags} --msg-template={msg_template} {apps} | "
            "tee {report_dir}/pylint.report".format(
                pythonpath_prefix=pythonpath_prefix,
                flags=" ".join(flags),
                msg_template='"{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}"',
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
@cmdopts([
    ("compare-branch=", "b", "Branch to compare against, defaults to origin/master"),
    ("percentage=", "p", "fail if diff-quality is below this percentage"),
])
def run_quality(options):
    """
    Build the html diff quality reports, and print the reports to the console.
    :param: b, the branch to compare against, defaults to origin/master
    :param: p, diff-quality will fail if the quality percentage calculated is
        below this percentage. For example, if p is set to 80, and diff-quality finds
        quality of the branch vs the compare branch is less than 80%, then this task will fail.
        This threshold would be applied to both pep8 and pylint.
    """

    # Directory to put the diff reports in.
    # This makes the folder if it doesn't already exist.
    dquality_dir = (Env.REPORT_DIR / "diff_quality").makedirs_p()
    diff_quality_percentage_failure = False

    # Set the string, if needed, to be used for the diff-quality --compare-branch switch.
    compare_branch = getattr(options, 'compare_branch', None)
    compare_branch_string = ''
    if compare_branch:
        compare_branch_string = '--compare-branch={0}'.format(compare_branch)

    # Set the string, if needed, to be used for the diff-quality --fail-under switch.
    diff_threshold = int(getattr(options, 'percentage', -1))
    percentage_string = ''
    if diff_threshold > -1:
        percentage_string = '--fail-under={0}'.format(diff_threshold)

    # Generate diff-quality html report for pep8, and print to console
    # If pep8 reports exist, use those
    # Otherwise, `diff-quality` will call pep8 itself

    pep8_files = get_violations_reports("pep8")
    pep8_reports = u' '.join(pep8_files)

    try:
        sh(
            "diff-quality --violations=pep8 {pep8_reports} {percentage_string} "
            "{compare_branch_string} --html-report {dquality_dir}/diff_quality_pep8.html".format(
                pep8_reports=pep8_reports,
                percentage_string=percentage_string,
                compare_branch_string=compare_branch_string,
                dquality_dir=dquality_dir
            )
        )
    except BuildFailure, error_message:
        if is_percentage_failure(error_message):
            diff_quality_percentage_failure = True
        else:
            raise BuildFailure(error_message)

    # Generate diff-quality html report for pylint, and print to console
    # If pylint reports exist, use those
    # Otherwise, `diff-quality` will call pylint itself

    pylint_files = get_violations_reports("pylint")
    pylint_reports = u' '.join(pylint_files)

    pythonpath_prefix = (
        "PYTHONPATH=$PYTHONPATH:lms:lms/djangoapps:lms/lib:cms:cms/djangoapps:cms/lib:"
        "common:common/djangoapps:common/lib"
    )

    try:
        sh(
            "{pythonpath_prefix} diff-quality --violations=pylint "
            "{pylint_reports} {percentage_string} {compare_branch_string} "
            "--html-report {dquality_dir}/diff_quality_pylint.html ".format(
                pythonpath_prefix=pythonpath_prefix,
                pylint_reports=pylint_reports,
                percentage_string=percentage_string,
                compare_branch_string=compare_branch_string,
                dquality_dir=dquality_dir,
            )
        )
    except BuildFailure, error_message:
        if is_percentage_failure(error_message):
            diff_quality_percentage_failure = True
        else:
            raise BuildFailure(error_message)

    # If one of the diff-quality runs fails, then paver exits with an error when it is finished
    if diff_quality_percentage_failure:
        raise BuildFailure("Diff-quality failure(s).")


def is_percentage_failure(error_message):
    """
    When diff-quality is run with a threshold percentage, it ends with an exit code of 1. This bubbles up to
    paver with a subprocess return code error. If the subprocess exits with anything other than 1, raise
    a paver exception.
    """
    if "Subprocess return code: 1" not in error_message:
        return False
    else:
        return True


def get_violations_reports(violations_type):
    """
    Finds violations reports files by naming convention (e.g., all "pep8.report" files)
    """
    violations_files = []
    for subdir, _dirs, files in os.walk(os.path.join(Env.REPORT_DIR)):
        for f in files:
            if f == "{violations_type}.report".format(violations_type=violations_type):
                violations_files.append(os.path.join(subdir, f))
    return violations_files

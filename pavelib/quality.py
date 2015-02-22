"""
Check code quality using pep8, pylint, and diff_quality.
"""
from __future__ import print_function
from paver.easy import sh, task, cmdopts, needs, BuildFailure
import os
import re

from .utils.envs import Env

DIRECTORIES_TOP_LEVEL_COMMON = {
    'common',
    'openedx',
}

DIRECTORIES_TOP_LEVEL_SYSTEMS = {
    'cms',
    'docs',
    'lms',
    'pavelib',
    'scripts',
}

DIRECTORIES_TOP_LEVEL_ALL = set()
DIRECTORIES_TOP_LEVEL_ALL.update(DIRECTORIES_TOP_LEVEL_COMMON)
DIRECTORIES_TOP_LEVEL_ALL.update(DIRECTORIES_TOP_LEVEL_SYSTEMS)

DIRECTORIES_INNER = {
    'djangoapps',
    'lib',
}


def _get_path_list(system):
    """
    Gather a list of subdirectories within the system

    :param system: the system directory to search; e.g. 'lms', 'cms'
    :returns: a list of system subdirectories to be linted
    """
    paths = [
        system,
    ]

    for directory in DIRECTORIES_INNER:
        try:
            directories = os.listdir(os.path.join(system, directory))
        except OSError:
            pass
        else:
            paths.extend([
                directory
                for directory in directories
                if os.path.isdir(os.path.join(system, directory, directory))
            ])

    path_list = ' '.join(paths)
    return path_list


def _get_python_path_prefix(directory_system):
    """
    Build a string to specify the PYTHONPATH environment variable

    :param directory_system: the system directory to search; e.g. 'lms', 'cms'
    :returns str: a PYTHONPATH environment string for the command line
    """
    paths = {
        directory_system,
    }
    directories_all = set(DIRECTORIES_TOP_LEVEL_COMMON)
    directories_all.add(directory_system)
    for system in directories_all:
        for subsystem in DIRECTORIES_INNER:
            path = os.path.join(system, subsystem)
            paths.add(path)
    paths = ':'.join(paths)
    environment_python_path = "PYTHONPATH={paths}".format(
        paths=paths,
    )
    return environment_python_path


def _parse(options):
    """
    Parse command line options, setting sane defaults

    :param options: a Paver Options object
    :returns dict: containing: errors, system, limit
    """
    return {
        'errors': getattr(options, 'errors', False),
        'systems': getattr(options, 'system', ','.join(DIRECTORIES_TOP_LEVEL_ALL)).split(','),
        'limit': int(getattr(options, 'limit', -1)),
    }


@task
@needs('pavelib.prereqs.install_python_prereqs')
@cmdopts([
    ("system=", "s", "System to act on"),
])
def find_fixme(options):
    """
    Run pylint on system code, only looking for fixme items.
    """
    count = 0
    options = _parse(options)

    for system in options['systems']:
        report_dir = (Env.REPORT_DIR / system).makedirs_p()
        path_list = _get_path_list(system)
        environment_python_path = _get_python_path_prefix(system)
        sh(
            "{environment_python_path} pylint --disable R,C,W,E --enable=fixme "
            "--msg-template={msg_template} {path_list} "
            "| tee {report_dir}/pylint_fixme.report".format(
                environment_python_path=environment_python_path,
                msg_template='"{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}"',
                path_list=path_list,
                report_dir=report_dir
            )
        )
        count += _count_pylint_violations(
            "{report_dir}/pylint_fixme.report".format(report_dir=report_dir)
        )

    print("Number of pylint fixmes: " + str(count))


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
    options = _parse(options)

    for system in options['systems']:
        report_dir = (Env.REPORT_DIR / system).makedirs_p()

        flags = []
        if options['errors']:
            flags.append("--errors-only")

        path_list = _get_path_list(system)
        environment_python_path = _get_python_path_prefix(system)
        sh(
            "{environment_python_path} pylint {flags} --msg-template={msg_template} {path_list} | "
            "tee {report_dir}/pylint.report".format(
                environment_python_path=environment_python_path,
                flags=' '.join(flags),
                msg_template='"{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}"',
                path_list=path_list,
                report_dir=report_dir
            )
        )
        num_violations += _count_pylint_violations(
            "{report_dir}/pylint.report".format(report_dir=report_dir))

    print("Number of pylint violations: " + str(num_violations))
    if num_violations > options['limit'] > -1:
        raise Exception("Failed. Too many pylint violations. "
                        "The limit is {violations_limit}.".format(violations_limit=options['limit']))


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
    options = _parse(options)
    count = 0

    for system in options['systems']:
        report_dir = (Env.REPORT_DIR / system).makedirs_p()
        sh('pep8 {system} | tee {report_dir}/pep8.report'.format(system=system, report_dir=report_dir))
        count += _count_pep8_violations(
            "{report_dir}/pep8.report".format(report_dir=report_dir)
        )

    print("Number of pep8 violations: {count}".format(count=count))
    if count:
        raise Exception("Failed. Too many pep8 violations.")


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

    environment_python_path = (
        "PYTHONPATH=$PYTHONPATH:lms:lms/djangoapps:lms/lib:cms:cms/djangoapps:cms/lib:"
        "common:common/djangoapps:common/lib"
    )

    try:
        sh(
            "{environment_python_path} diff-quality --violations=pylint "
            "{pylint_reports} {percentage_string} {compare_branch_string} "
            "--html-report {dquality_dir}/diff_quality_pylint.html ".format(
                environment_python_path=environment_python_path,
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
    return "Subprocess return code: 1" in error_message


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

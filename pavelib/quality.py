"""
Check code quality using PEP8, Pylint, and diff_quality.
"""
from __future__ import print_function
import os

from paver.easy import task, cmdopts, needs, BuildFailure

from pavelib.utils.wrapper import pep8 as pep8_wrapper
from pavelib.utils.wrapper import pylint as pylint_wrapper
from pavelib.utils.wrapper import get_clean_report_directory
from pavelib.utils.wrapper import get_pylint_reports
from pavelib.utils.wrapper import get_python_path
from pavelib.utils.cmd import shell
from pavelib.utils.envs import Env

ALL_SERVICES = [
    'lms',
    'cms',
    'common',
]


@task
@needs('pavelib.prereqs.install_python_prereqs')
@cmdopts([
    ('system=', 's', 'System to act on'),
])
def find_fixme(options):
    """
    Run Pylint on system code, only looking for FIXME items
    """
    systems = getattr(options, 'system', ','.join(ALL_SERVICES)).split(',')
    flags = [
        '--disable R,C,W,E',
        '--enable=fixme',
    ]
    pylint_wrapper('fixme', systems, *flags)


@task
@needs('pavelib.prereqs.install_python_prereqs')
@cmdopts([
    ('system=', 's', 'System to act on'),
    ('errors', 'e', 'Check for errors only'),
    ('limit=', 'l', 'Limit for number of acceptable violations'),
])
def run_pylint(options):
    """
    Run Pylint on system code.

    When violations limit is passed in,
    fail the task if too many violations are found.
    """
    limit = int(getattr(options, 'limit', -1))
    errors = getattr(options, 'errors', False)
    systems = getattr(options, 'system', ','.join(ALL_SERVICES)).split(',')
    flags = []
    if errors:
        flags.append('--errors-only')
    count = pylint_wrapper('pylint', systems, *flags)
    if count > limit > -1:
        raise Exception((
            "Failed. Too many Pylint violations. "
            "The limit is {limit}."
        ).format(
            limit=limit,
        ))


@task
@needs('pavelib.prereqs.install_python_prereqs')
@cmdopts([
    ('system=', 's', 'System to act on'),
])
def run_pep8(options):
    """
    Run PEP8 on system code.
    :raise Exception: if any violations are found
    """
    systems = getattr(options, 'system', '')
    systems = systems.split(',')
    count = pep8_wrapper(systems)
    if count:
        raise Exception(
            "Too many PEP8 violations. Number of violations found: {count}.".format(
                count=count,
            )
        )


@task
@needs('pavelib.prereqs.install_python_prereqs')
def run_complexity():
    """
    Uses radon to examine cyclomatic complexity.
    For additional details on radon, see http://radon.readthedocs.org/
    """
    system_string = 'cms/ lms/ common/ openedx/'
    print('--> Calculating cyclomatic complexity of files...')
    try:
        shell(
            'radon',
            'cc',
            system_string,
            '--total-average',
        )
    except BuildFailure:
        print('ERROR: Unable to calculate python-only code-complexity.')


@task
@needs('pavelib.prereqs.install_python_prereqs')
@cmdopts([
    ('compare-branch=', 'b', 'Branch to compare against, defaults to origin/master'),
    ('percentage=', 'p', 'Fail if diff-quality is below this percentage'),
])
def run_quality(options):
    """
    Build the html diff quality reports, and print the reports to the console.
    :param: b, the branch to compare against, defaults to origin/master
    :param: p, diff-quality will fail if the quality percentage calculated is
        below this percentage. For example, if p is set to 80, and diff-quality finds
        quality of the branch vs the compare branch is less than 80%, then this task will fail.
        This threshold would be applied to both PEP8 and Pylint.
    """

    directory_report = get_clean_report_directory('diff_quality')
    percentage_failure = False

    compare_branch = getattr(options, 'compare_branch', '')
    if compare_branch:
        compare_branch = "--compare-branch={0}".format(compare_branch)

    diff_threshold = int(getattr(options, 'percentage', -1))
    percentage_string = ''
    if diff_threshold > -1:
        percentage_string = '--fail-under={0}'.format(diff_threshold)

    pep8_count = pep8_wrapper()
    percentage_failure = pep8_count > 0

    pylint_files = get_pylint_reports()
    pylint_reports = u' '.join(pylint_files)
    html_report = "{directory_report}/diff_quality_pylint.html ".format(
        directory_report=directory_report,
    )
    pythonpath_prefix = get_python_path('lms', 'cms')
    try:
        shell(
            pythonpath_prefix,
            'diff-quality',
            '--violations=pylint',
            pylint_reports,
            percentage_string,
            compare_branch,
            '--html-report',
            html_report,
        )
    except BuildFailure, error_message:
        if 'Subprocess return code: 1' in error_message:
            percentage_failure = True
        else:
            raise BuildFailure(error_message)
    if percentage_failure:
        raise BuildFailure('Diff-quality failure(s).')

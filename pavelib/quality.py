"""
Check code quality using pep8, pylint, and diff_quality.
"""
from paver.easy import sh, task, cmdopts, needs, BuildFailure
import os
import re

from .utils.envs import Env

ALL_SYSTEMS = 'lms,cms,common,openedx,pavelib'


def top_python_dirs(dirname):
    """
    Find the directories to start from in order to find all the Python files in `dirname`.
    """
    top_dirs = []

    dir_init = os.path.join(dirname, "__init__.py")
    if os.path.exists(dir_init):
        top_dirs.append(dirname)

    for directory in ['djangoapps', 'lib']:
        subdir = os.path.join(dirname, directory)
        subdir_init = os.path.join(subdir, "__init__.py")
        if os.path.exists(subdir) and not os.path.exists(subdir_init):
            dirs = os.listdir(subdir)
            top_dirs.extend(d for d in dirs if os.path.isdir(os.path.join(subdir, d)))

    return top_dirs


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
    systems = getattr(options, 'system', ALL_SYSTEMS).split(',')

    for system in systems:
        # Directory to put the pylint report in.
        # This makes the folder if it doesn't already exist.
        report_dir = (Env.REPORT_DIR / system).makedirs_p()

        apps_list = ' '.join(top_python_dirs(system))

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

    print "Number of pylint fixmes: " + str(num_fixme)


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
    systems = getattr(options, 'system', ALL_SYSTEMS).split(',')

    # Make sure the metrics subdirectory exists
    Env.METRICS_DIR.makedirs_p()

    for system in systems:
        # Directory to put the pylint report in.
        # This makes the folder if it doesn't already exist.
        report_dir = (Env.REPORT_DIR / system).makedirs_p()

        flags = []
        if errors:
            flags.append("--errors-only")

        apps_list = ' '.join(top_python_dirs(system))

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

    # Print number of violations to log
    violations_count_str = "Number of pylint violations: " + str(num_violations)
    print violations_count_str

    # Also write the number of violations to a file
    with open(Env.METRICS_DIR / "pylint", "w") as f:
        f.write(violations_count_str)

    # Fail number of violations is greater than the limit
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
    pylint_pattern = re.compile(r".(\d+):\ \[(\D\d+.+\]).")

    for line in open(report_file):
        violation_list_for_line = pylint_pattern.split(line)
        # If the string is parsed into four parts, then we've found a violation. Example of split parts:
        # test file, line number, violation name, violation details
        if len(violation_list_for_line) == 4:
            num_violations_report += 1
    return num_violations_report


def _get_pep8_violations():
    """
    Runs pep8. Returns a tuple of (number_of_violations, violations_string)
    where violations_string is a string of all pep8 violations found, separated
    by new lines.
    """
    report_dir = (Env.REPORT_DIR / 'pep8')
    report_dir.rmtree(ignore_errors=True)
    report_dir.makedirs_p()

    # Make sure the metrics subdirectory exists
    Env.METRICS_DIR.makedirs_p()

    sh('pep8 . | tee {report_dir}/pep8.report -a'.format(report_dir=report_dir))

    count, violations_list = _pep8_violations(
        "{report_dir}/pep8.report".format(report_dir=report_dir)
    )

    return (count, violations_list)


def _pep8_violations(report_file):
    """
    Returns a tuple of (num_violations, violations_list) for all
    pep8 violations in the given report_file.
    """
    with open(report_file) as f:
        violations_list = f.readlines()
    num_lines = len(violations_list)
    return num_lines, violations_list


@task
@needs('pavelib.prereqs.install_python_prereqs')
@cmdopts([
    ("system=", "s", "System to act on"),
])
def run_pep8(options):  # pylint: disable=unused-argument
    """
    Run pep8 on system code.
    Fail the task if any violations are found.
    """
    (count, violations_list) = _get_pep8_violations()
    violations_list = ''.join(violations_list)

    # Print number of violations to log
    violations_count_str = "Number of pep8 violations: {count}".format(count=count)
    print violations_count_str
    print violations_list

    # Also write the number of violations to a file
    with open(Env.METRICS_DIR / "pep8", "w") as f:
        f.write(violations_count_str + '\n\n')
        f.write(violations_list)

    # Fail if any violations are found
    if count:
        failure_string = "Too many pep8 violations. " + violations_count_str
        failure_string += "\n\nViolations:\n{violations_list}".format(violations_list=violations_list)
        raise Exception(failure_string)


@task
@needs('pavelib.prereqs.install_python_prereqs')
def run_complexity():
    """
    Uses radon to examine cyclomatic complexity.
    For additional details on radon, see http://radon.readthedocs.org/
    """
    system_string = 'cms/ lms/ common/ openedx/'
    print "--> Calculating cyclomatic complexity of files..."
    try:
        sh(
            "radon cc {system_string} --total-average".format(
                system_string=system_string
            )
        )
    except BuildFailure:
        print "ERROR: Unable to calculate python-only code-complexity."


@task
@needs('pavelib.prereqs.install_node_prereqs')
@cmdopts([
    ("limit=", "l", "limit for number of acceptable violations"),
])
def run_jshint(options):
    """
    Runs jshint on static asset directories
    """

    violations_limit = int(getattr(options, 'limit', -1))

    jshint_report_dir = (Env.REPORT_DIR / "jshint")
    jshint_report = jshint_report_dir / "jshint.report"
    _prepare_report_dir(jshint_report_dir)

    jshint_directories = ["common/static/js", "cms/static/js", "lms/static/js"]

    sh(
        "jshint {list} --config .jshintrc >> {jshint_report}".format(
            list=(" ".join(jshint_directories)), jshint_report=jshint_report
        ),
        ignore_error=True
    )
    num_violations = _get_count_from_last_line(jshint_report)

    if not num_violations:
        raise BuildFailure("Error in calculating total number of violations.")

    # Record the metric
    _write_metric(str(num_violations), (Env.METRICS_DIR / "jshint"))

    # Fail if number of violations is greater than the limit
    if num_violations > violations_limit > -1:
        raise Exception(
            "JSHint Failed. Too many violations ({count}).\nThe limit is {violations_limit}.".format(
                count=num_violations, violations_limit=violations_limit
            )
        )


def _write_metric(metric, filename):
    """
    Write a given metric to a given file
    Used for things like reports/metrics/jshint, which will simply tell you the number of
    jshint violations found
    """
    with open(filename, "w") as metric_file:
        metric_file.write(metric)


def _prepare_report_dir(dir_name):
    """
    Sets a given directory to a created, but empty state
    """
    dir_name.rmtree_p()
    dir_name.mkdir_p()


def _get_last_report_line(filename):
    """
    Returns the last line of a given file. Used for getting output from quality output files.
    """
    with open(filename, 'r') as report_file:
        lines = report_file.readlines()
        return lines[len(lines) - 1]


def _get_count_from_last_line(filename):
    """
    This will return the number in a line that looks something like "3000 errors found". It is returning
    the digits only (as an integer).
    """
    last_line = _get_last_report_line(filename)
    try:
        return int(re.search(r'^\d+', last_line).group(0))
    except AttributeError:
        return None


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

    def _pep8_output(count, violations_list, is_html=False):
        """
        Given a count & list of pep8 violations, pretty-print the pep8 output.
        If `is_html`, will print out with HTML markup.
        """
        if is_html:
            lines = ['<body>\n']
            sep = '-------------<br/>\n'
            title = "<h1>Quality Report: pep8</h1>\n"
            violations_bullets = ''.join(
                ['<li>{violation}</li><br/>\n'.format(violation=violation) for violation in violations_list]
            )
            violations_str = '<ul>\n{bullets}</ul>\n'.format(bullets=violations_bullets)
            violations_count_str = "<b>Violations</b>: {count}<br/>\n"
            fail_line = "<b>FAILURE</b>: pep8 count should be 0<br/>\n"
        else:
            lines = []
            sep = '-------------\n'
            title = "Quality Report: pep8\n"
            violations_str = ''.join(violations_list)
            violations_count_str = "Violations: {count}\n"
            fail_line = "FAILURE: pep8 count should be 0\n"

        violations_count_str = violations_count_str.format(count=count)

        lines.extend([sep, title, sep, violations_str, sep, violations_count_str])

        if count > 0:
            lines.append(fail_line)
        lines.append(sep + '\n')
        if is_html:
            lines.append('</body>')

        return ''.join(lines)

    # Run pep8 directly since we have 0 violations on master
    (count, violations_list) = _get_pep8_violations()

    # Print number of violations to log
    print _pep8_output(count, violations_list)

    # Also write the number of violations to a file
    with open(dquality_dir / "diff_quality_pep8.html", "w") as f:
        f.write(_pep8_output(count, violations_list, is_html=True))

    if count > 0:
        diff_quality_percentage_failure = True

    # ----- Set up for diff-quality pylint call -----
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

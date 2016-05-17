"""
Check code quality using pep8, pylint, and diff_quality.
"""
from paver.easy import sh, task, cmdopts, needs, BuildFailure
import json
import os
import re

from openedx.core.djangolib.markup import HTML

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
            "PYTHONPATH={system}/djangoapps:common/djangoapps:common/lib".format(
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
            "PYTHONPATH={system}/djangoapps:common/djangoapps:common/lib".format(
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
        raise BuildFailure("Failed. Too many pylint violations. "
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
        raise BuildFailure(failure_string)


@task
@needs('pavelib.prereqs.install_python_prereqs')
def run_complexity():
    """
    Uses radon to examine cyclomatic complexity.
    For additional details on radon, see http://radon.readthedocs.org/
    """
    system_string = 'cms/ lms/ common/ openedx/'
    complexity_report_dir = (Env.REPORT_DIR / "complexity")
    complexity_report = complexity_report_dir / "python_complexity.log"

    # Ensure directory structure is in place: metrics dir, and an empty complexity report dir.
    Env.METRICS_DIR.makedirs_p()
    _prepare_report_dir(complexity_report_dir)

    print "--> Calculating cyclomatic complexity of python files..."
    try:
        sh(
            "radon cc {system_string} --total-average > {complexity_report}".format(
                system_string=system_string,
                complexity_report=complexity_report
            )
        )
        complexity_metric = _get_count_from_last_line(complexity_report, "python_complexity")
        _write_metric(
            complexity_metric,
            (Env.METRICS_DIR / "python_complexity")
        )
        print "--> Python cyclomatic complexity report complete."
        print "radon cyclomatic complexity score: {metric}".format(metric=str(complexity_metric))

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

    sh(
        "jshint . --config .jshintrc >> {jshint_report}".format(
            jshint_report=jshint_report
        ),
        ignore_error=True
    )

    try:
        num_violations = int(_get_count_from_last_line(jshint_report, "jshint"))
    except TypeError:
        raise BuildFailure(
            "Error. Number of jshint violations could not be found in {jshint_report}".format(
                jshint_report=jshint_report
            )
        )

    # Record the metric
    _write_metric(num_violations, (Env.METRICS_DIR / "jshint"))

    # Fail if number of violations is greater than the limit
    if num_violations > violations_limit > -1:
        raise BuildFailure(
            "JSHint Failed. Too many violations ({count}).\nThe limit is {violations_limit}.".format(
                count=num_violations, violations_limit=violations_limit
            )
        )


@task
@needs('pavelib.prereqs.install_python_prereqs')
@cmdopts([
    ("thresholds=", "t", "json containing limit for number of acceptable violations per rule"),
])
def run_safelint(options):
    """
    Runs safe_template_linter.py on the codebase
    """

    thresholds_option = getattr(options, 'thresholds', '{}')
    try:
        violation_thresholds = json.loads(thresholds_option)
    except ValueError:
        violation_thresholds = None
    if isinstance(violation_thresholds, dict) is False or \
            any(key not in ("total", "rules") for key in violation_thresholds.keys()):

        raise BuildFailure(
            """Error. Thresholds option "{thresholds_option}" was not supplied using proper format.\n"""
            """Here is a properly formatted example, '{{"total":100,"rules":{{"javascript-escape":0}}}}' """
            """with property names in double-quotes.""".format(
                thresholds_option=thresholds_option
            )
        )

    safelint_script = "safe_template_linter.py"
    safelint_report_dir = (Env.REPORT_DIR / "safelint")
    safelint_report = safelint_report_dir / "safelint.report"
    _prepare_report_dir(safelint_report_dir)

    sh(
        "{repo_root}/scripts/{safelint_script} --rule-totals >> {safelint_report}".format(
            repo_root=Env.REPO_ROOT,
            safelint_script=safelint_script,
            safelint_report=safelint_report,
        ),
        ignore_error=True
    )

    safelint_counts = _get_safelint_counts(safelint_report)

    try:
        metrics_str = "Number of {safelint_script} violations: {num_violations}\n".format(
            safelint_script=safelint_script, num_violations=int(safelint_counts['total'])
        )
        if 'rules' in safelint_counts and any(safelint_counts['rules']):
            metrics_str += "\n"
            rule_keys = sorted(safelint_counts['rules'].keys())
            for rule in rule_keys:
                metrics_str += "{rule} violations: {count}\n".format(
                    rule=rule,
                    count=int(safelint_counts['rules'][rule])
                )
    except TypeError:
        raise BuildFailure(
            "Error. Number of {safelint_script} violations could not be found in {safelint_report}".format(
                safelint_script=safelint_script, safelint_report=safelint_report
            )
        )

    metrics_report = (Env.METRICS_DIR / "safelint")
    # Record the metric
    _write_metric(metrics_str, metrics_report)
    # Print number of violations to log.
    sh("cat {metrics_report}".format(metrics_report=metrics_report), ignore_error=True)

    error_message = ""

    # Test total violations against threshold.
    if 'total' in violation_thresholds.keys():
        if violation_thresholds['total'] < safelint_counts['total']:
            error_message = "Too many violations total ({count}).\nThe limit is {violations_limit}.".format(
                count=safelint_counts['total'], violations_limit=violation_thresholds['total']
            )

    # Test rule violations against thresholds.
    if 'rules' in violation_thresholds:
        threshold_keys = sorted(violation_thresholds['rules'].keys())
        for threshold_key in threshold_keys:
            if threshold_key not in safelint_counts['rules']:
                error_message += (
                    "\nNumber of {safelint_script} violations for {rule} could not be found in "
                    "{safelint_report}."
                ).format(
                    safelint_script=safelint_script, rule=threshold_key, safelint_report=safelint_report
                )
            elif violation_thresholds['rules'][threshold_key] < safelint_counts['rules'][threshold_key]:
                error_message += \
                    "\nToo many {rule} violations ({count}).\nThe {rule} limit is {violations_limit}.".format(
                        rule=threshold_key, count=safelint_counts['rules'][threshold_key],
                        violations_limit=violation_thresholds['rules'][threshold_key],
                    )

    if error_message is not "":
        raise BuildFailure(
            "SafeTemplateLinter Failed.\n{error_message}\n"
            "See {safelint_report} or run the following command to hone in on the problem:\n"
            "  ./scripts/safe-commit-linter.sh -h".format(
                error_message=error_message, safelint_report=safelint_report
            )
        )


@task
@needs('pavelib.prereqs.install_python_prereqs')
def run_safecommit_report():
    """
    Runs safe-commit-linter.sh on the current branch.
    """
    safecommit_script = "safe-commit-linter.sh"
    safecommit_report_dir = (Env.REPORT_DIR / "safecommit")
    safecommit_report = safecommit_report_dir / "safecommit.report"
    _prepare_report_dir(safecommit_report_dir)

    sh(
        "{repo_root}/scripts/{safecommit_script} | tee {safecommit_report}".format(
            repo_root=Env.REPO_ROOT,
            safecommit_script=safecommit_script,
            safecommit_report=safecommit_report,
        ),
        ignore_error=True
    )

    safecommit_count = _get_safecommit_count(safecommit_report)

    try:
        num_violations = int(safecommit_count)
    except TypeError:
        raise BuildFailure(
            "Error. Number of {safecommit_script} violations could not be found in {safecommit_report}".format(
                safecommit_script=safecommit_script, safecommit_report=safecommit_report
            )
        )

    # Print number of violations to log.
    violations_count_str = "Number of {safecommit_script} violations: {num_violations}\n".format(
        safecommit_script=safecommit_script, num_violations=num_violations
    )

    # Record the metric
    metrics_report = (Env.METRICS_DIR / "safecommit")
    _write_metric(violations_count_str, metrics_report)
    # Output report to console.
    sh("cat {metrics_report}".format(metrics_report=metrics_report), ignore_error=True)


def _write_metric(metric, filename):
    """
    Write a given metric to a given file
    Used for things like reports/metrics/jshint, which will simply tell you the number of
    jshint violations found
    """
    with open(filename, "w") as metric_file:
        metric_file.write(str(metric))


def _prepare_report_dir(dir_name):
    """
    Sets a given directory to a created, but empty state
    """
    dir_name.rmtree_p()
    dir_name.mkdir_p()


def _get_report_contents(filename, last_line_only=False):
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
    file_not_found_message = "The following log file could not be found: {file}".format(file=filename)
    if os.path.isfile(filename):
        with open(filename, 'r') as report_file:
            if last_line_only:
                lines = report_file.readlines()
                return lines[len(lines) - 1]
            else:
                return report_file.read()
    else:
        # Raise a build error if the file is not found
        raise BuildFailure(file_not_found_message)


def _get_count_from_last_line(filename, file_type):
    """
    This will return the number in the last line of a file.
    It is returning only the value (as a floating number).
    """
    last_line = _get_report_contents(filename, last_line_only=True)
    if file_type is "python_complexity":
        # Example of the last line of a complexity report: "Average complexity: A (1.93953443446)"
        regex = r'\d+.\d+'
    else:
        # Example of the last line of a jshint report (for example): "3482 errors"
        regex = r'^\d+'

    try:
        return float(re.search(regex, last_line).group(0))
    # An AttributeError will occur if the regex finds no matches.
    # A ValueError will occur if the returned regex cannot be cast as a float.
    except (AttributeError, ValueError):
        return None


def _get_safelint_counts(filename):
    """
    This returns a dict of violations from the safelint report.

    Arguments:
        filename: The name of the safelint report.

    Returns:
        A dict containing the following:
            rules: A dict containing the count for each rule as follows:
                violation-rule-id: N, where N is the number of violations
            total: M, where M is the number of total violations

    """
    report_contents = _get_report_contents(filename)
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


def _get_safecommit_count(filename):
    """
    Returns the violation count from the safecommit report.

    Arguments:
        filename: The name of the safecommit report.

    Returns:
        The count of safecommit violations, or None if there is  a problem.

    """
    report_contents = _get_report_contents(filename)

    if 'No files linted' in report_contents:
        return 0

    file_count_regex = re.compile(r"^(?P<count>\d+) violations total", re.MULTILINE)
    try:
        validation_count = None
        for count_match in file_count_regex.finditer(report_contents):
            if validation_count is None:
                validation_count = 0
            validation_count += int(count_match.group('count'))
        return validation_count
    except ValueError:
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

    # Save the pass variable. It will be set to false later if failures are detected.
    diff_quality_percentage_pass = True

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
                [HTML('<li>{violation}</li><br/>\n').format(violation=violation) for violation in violations_list]
            )
            violations_str = HTML('<ul>\n{bullets}</ul>\n').format(bullets=HTML(violations_bullets))
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
        diff_quality_percentage_pass = False

    # ----- Set up for diff-quality pylint call -----
    # Set the string, if needed, to be used for the diff-quality --compare-branch switch.
    compare_branch = getattr(options, 'compare_branch', None)
    compare_branch_string = u''
    if compare_branch:
        compare_branch_string = u'--compare-branch={0}'.format(compare_branch)

    # Set the string, if needed, to be used for the diff-quality --fail-under switch.
    diff_threshold = int(getattr(options, 'percentage', -1))
    percentage_string = u''
    if diff_threshold > -1:
        percentage_string = u'--fail-under={0}'.format(diff_threshold)

    # Generate diff-quality html report for pylint, and print to console
    # If pylint reports exist, use those
    # Otherwise, `diff-quality` will call pylint itself

    pylint_files = get_violations_reports("pylint")
    pylint_reports = u' '.join(pylint_files)
    jshint_files = get_violations_reports("jshint")
    jshint_reports = u' '.join(jshint_files)

    pythonpath_prefix = (
        "PYTHONPATH=$PYTHONPATH:lms:lms/djangoapps:cms:cms/djangoapps:"
        "common:common/djangoapps:common/lib"
    )

    # run diff-quality for pylint.
    if not run_diff_quality(
            violations_type="pylint",
            prefix=pythonpath_prefix,
            reports=pylint_reports,
            percentage_string=percentage_string,
            branch_string=compare_branch_string,
            dquality_dir=dquality_dir
    ):
        diff_quality_percentage_pass = False

    # run diff-quality for jshint.
    if not run_diff_quality(
            violations_type="jshint",
            prefix=pythonpath_prefix,
            reports=jshint_reports,
            percentage_string=percentage_string,
            branch_string=compare_branch_string,
            dquality_dir=dquality_dir
    ):
        diff_quality_percentage_pass = False

    # If one of the quality runs fails, then paver exits with an error when it is finished
    if not diff_quality_percentage_pass:
        raise BuildFailure("Diff-quality failure(s).")


def run_diff_quality(
        violations_type=None, prefix=None, reports=None, percentage_string=None, branch_string=None, dquality_dir=None
):
    """
    This executes the diff-quality commandline tool for the given violation type (e.g., pylint, jshint).
    If diff-quality fails due to quality issues, this method returns False.

    """
    try:
        sh(
            "{pythonpath_prefix} diff-quality --violations={type} "
            "{reports} {percentage_string} {compare_branch_string} "
            "--html-report {dquality_dir}/diff_quality_{type}.html ".format(
                type=violations_type,
                pythonpath_prefix=prefix,
                reports=reports,
                percentage_string=percentage_string,
                compare_branch_string=branch_string,
                dquality_dir=dquality_dir,
            )
        )
        return True
    except BuildFailure, error_message:
        if is_percentage_failure(error_message):
            return False
        else:
            raise BuildFailure(error_message)


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

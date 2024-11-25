"""  # lint-amnesty, pylint: disable=django-not-configured
Check code quality using pycodestyle, pylint, and diff_quality.
"""

import json
import os
import re
from datetime import datetime
from xml.sax.saxutils import quoteattr

from paver.easy import BuildFailure, cmdopts, needs, sh, task

<<<<<<< HEAD
from openedx.core.djangolib.markup import HTML

=======
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
from .utils.envs import Env
from .utils.timer import timed

ALL_SYSTEMS = 'lms,cms,common,openedx,pavelib,scripts'
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
    raise BuildFailure(message)


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

    modules_to_remove = ['__pycache__']
    for module in modules_to_remove:
        if module in top_dirs:
            top_dirs.remove(module)

    return top_dirs


<<<<<<< HEAD
@task
@needs('pavelib.prereqs.install_python_prereqs')
@cmdopts([
    ("system=", "s", "System to act on"),
])
@timed
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

        cmd = (
            "pylint --disable all --enable=fixme "
            "--output-format=parseable {apps} "
            "> {report_dir}/pylint_fixme.report".format(
                apps=apps_list,
                report_dir=report_dir
            )
        )

        sh(cmd, ignore_error=True)

        num_fixme += _count_pylint_violations(
            f"{report_dir}/pylint_fixme.report")

    print("Number of pylint fixmes: " + str(num_fixme))


def _get_pylint_violations(systems=ALL_SYSTEMS.split(','), errors_only=False, clean=True):
    """
    Runs pylint. Returns a tuple of (number_of_violations, list_of_violations)
    where list_of_violations is a list of all pylint violations found, separated
    by new lines.
    """
    # Make sure the metrics subdirectory exists
    Env.METRICS_DIR.makedirs_p()

    num_violations = 0
    violations_list = []

    for system in systems:
        # Directory to put the pylint report in.
        # This makes the folder if it doesn't already exist.
        report_dir = (Env.REPORT_DIR / system).makedirs_p()

        flags = []
        if errors_only:
            flags.append("--errors-only")

        apps_list = ' '.join(top_python_dirs(system))

        system_report = report_dir / 'pylint.report'
        if clean or not system_report.exists():
            sh(
                "export DJANGO_SETTINGS_MODULE={env}.envs.test; "
                "pylint {flags} --output-format=parseable {apps} "
                "> {report_dir}/pylint.report".format(
                    flags=" ".join(flags),
                    apps=apps_list,
                    report_dir=report_dir,
                    env=('cms' if system == 'cms' else 'lms')
                ),
                ignore_error=True,
            )

        num_violations += _count_pylint_violations(system_report)
        with open(system_report) as report_contents:
            violations_list.extend(report_contents)

    # Print number of violations to log
    return num_violations, violations_list


@task
@needs('pavelib.prereqs.install_python_prereqs')
@cmdopts([
    ("system=", "s", "System to act on"),
    ("errors", "e", "Check for errors only"),
])
@timed
def run_pylint(options):
    """
    Run pylint on system code. When violations limit is passed in,
    fail the task if too many violations are found.
    """
    errors = getattr(options, 'errors', False)
    systems = getattr(options, 'system', ALL_SYSTEMS).split(',')
    result_name = 'pylint_{}'.format('_'.join(systems))

    num_violations, violations_list = _get_pylint_violations(systems, errors)

    # Print number of violations to log
    violations_count_str = "Number of pylint violations: " + str(num_violations)
    print(violations_count_str)

    # Also write the number of violations to a file
    with open(Env.METRICS_DIR / "pylint", "w") as f:
        f.write(violations_count_str)

    # Fail if there are violations found in pylint report.
    if num_violations > 0:
        failure_message = "FAILURE: Pylint violations found.\n"
        for violation in violations_list:
            failure_message += violation  # lint-amnesty, pylint: disable=consider-using-join
        fail_quality(result_name, failure_message)
    else:
        write_junit_xml(result_name)


def _count_pylint_violations(report_file):
    """
    Parses a pylint report line-by-line and determines the number of violations reported
    """
    num_violations_report = 0
    # An example string:
    # xmodule/xmodule/tests/test_conditional.py:21: [C0111(missing-docstring), DummySystem] Missing docstring
    # More examples can be found in the unit tests for this method
    pylint_pattern = re.compile(r".(\d+):\ \[(\D\d+.+\]).")

    for line in open(report_file):
        violation_list_for_line = pylint_pattern.split(line)
        # If the string is parsed into four parts, then we've found a violation. Example of split parts:
        # test file, line number, violation name, violation details
        if len(violation_list_for_line) == 4:
            num_violations_report += 1
    return num_violations_report


=======
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
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
        sh(f'pycodestyle . | tee {report} -a')

    violations_list = _pep8_violations(report)

    return len(violations_list), violations_list


def _pep8_violations(report_file):
    """
    Returns the list of all PEP 8 violations in the given report_file.
    """
    with open(report_file) as f:
        return f.readlines()


@task
<<<<<<< HEAD
@needs('pavelib.prereqs.install_python_prereqs')
=======
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
@cmdopts([
    ("system=", "s", "System to act on"),
])
@timed
def run_pep8(options):  # pylint: disable=unused-argument
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


@task
@needs(
    'pavelib.prereqs.install_node_prereqs',
    'pavelib.utils.test.utils.ensure_clean_package_lock',
)
@cmdopts([
    ("limit=", "l", "limit for number of acceptable violations"),
])
@timed
def run_eslint(options):
    """
    Runs eslint on static asset directories.
    If limit option is passed, fails build if more violations than the limit are found.
    """

    eslint_report_dir = (Env.REPORT_DIR / "eslint")
    eslint_report = eslint_report_dir / "eslint.report"
    _prepare_report_dir(eslint_report_dir)
    violations_limit = int(getattr(options, 'limit', -1))

    sh(
        "node --max_old_space_size=4096 node_modules/.bin/eslint "
        "--ext .js --ext .jsx --format=compact . | tee {eslint_report}".format(
            eslint_report=eslint_report
        ),
        ignore_error=True
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

    # Record the metric
    _write_metric(num_violations, (Env.METRICS_DIR / "eslint"))

    # Fail if number of violations is greater than the limit
    if num_violations > violations_limit > -1:
        fail_quality(
            'eslint',
            "FAILURE: Too many eslint violations ({count}).\nThe limit is {violations_limit}.".format(
                count=num_violations, violations_limit=violations_limit
            )
        )
    else:
        write_junit_xml('eslint')


def _get_stylelint_violations():
    """
    Returns the number of Stylelint violations.
    """
    stylelint_report_dir = (Env.REPORT_DIR / "stylelint")
    stylelint_report = stylelint_report_dir / "stylelint.report"
    _prepare_report_dir(stylelint_report_dir)
    formatter = 'node_modules/stylelint-formatter-pretty'

    sh(
        "stylelint **/*.scss --custom-formatter={formatter} | tee {stylelint_report}".format(
            formatter=formatter,
            stylelint_report=stylelint_report,
        ),
        ignore_error=True
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


@task
@needs('pavelib.prereqs.install_node_prereqs')
@cmdopts([
    ("limit=", "l", "limit for number of acceptable violations"),
])
@timed
def run_stylelint(options):
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


@task
@needs('pavelib.prereqs.install_python_prereqs')
@cmdopts([
    ("thresholds=", "t", "json containing limit for number of acceptable violations per rule"),
])
@timed
def run_xsslint(options):
    """
    Runs xsslint/xss_linter.py on the codebase
    """

    thresholds_option = getattr(options, 'thresholds', '{}')
    try:
        violation_thresholds = json.loads(thresholds_option)
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
    xsslint_report_dir = (Env.REPORT_DIR / "xsslint")
    xsslint_report = xsslint_report_dir / "xsslint.report"
    _prepare_report_dir(xsslint_report_dir)

    sh(
        "{repo_root}/scripts/xsslint/{xsslint_script} --rule-totals --config={cfg_module} >> {xsslint_report}".format(
            repo_root=Env.REPO_ROOT,
            xsslint_script=xsslint_script,
            xsslint_report=xsslint_report,
            cfg_module='scripts.xsslint_config'
        ),
        ignore_error=True
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

    metrics_report = (Env.METRICS_DIR / "xsslint")
    # Record the metric
    _write_metric(metrics_str, metrics_report)
    # Print number of violations to log.
    sh(f"cat {metrics_report}", ignore_error=True)

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
        write_junit_xml('xsslint')


def _write_metric(metric, filename):
    """
    Write a given metric to a given file
    Used for things like reports/metrics/eslint, which will simply tell you the number of
    eslint violations found
    """
    Env.METRICS_DIR.makedirs_p()

    with open(filename, "w") as metric_file:
        metric_file.write(str(metric))


def _prepare_report_dir(dir_name):
    """
    Sets a given directory to a created, but empty state
    """
    dir_name.rmtree_p()
    dir_name.mkdir_p()


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


@task
@needs('pavelib.prereqs.install_python_prereqs')
@cmdopts([
    ("report-dir=", "r", "Directory in which to put PII reports"),
])
@timed
def run_pii_check(options):
    """
    Guarantee that all Django models are PII-annotated.
    """
    pii_report_name = 'pii'
    default_report_dir = (Env.REPORT_DIR / pii_report_name)
    report_dir = getattr(options, 'report_dir', default_report_dir)
    output_file = os.path.join(report_dir, 'pii_check_{}.report')
    env_report = []
    pii_check_passed = True
    for env_name, env_settings_file in (("CMS", "cms.envs.test"), ("LMS", "lms.envs.test")):
        try:
            print()
            print(f"Running {env_name} PII Annotation check and report")
            print("-" * 45)
            run_output_file = str(output_file).format(env_name.lower())
            sh(
                "mkdir -p {} && "  # lint-amnesty, pylint: disable=duplicate-string-formatting-argument
                "export DJANGO_SETTINGS_MODULE={}; "
                "code_annotations django_find_annotations "
                "--config_file .pii_annotations.yml --report_path {} --app_name {} "
                "--lint --report --coverage | tee {}".format(
                    report_dir, env_settings_file, report_dir, env_name.lower(), run_output_file
                )
            )
            uncovered_model_count, pii_check_passed_env, full_log = _extract_missing_pii_annotations(run_output_file)
            env_report.append((
                uncovered_model_count,
                full_log,
            ))

        except BuildFailure as error_message:
            fail_quality(pii_report_name, f'FAILURE: {error_message}')

        if not pii_check_passed_env:
            pii_check_passed = False

    # Determine which suite is the worst offender by obtaining the max() keying off uncovered_count.
    uncovered_count, full_log = max(env_report, key=lambda r: r[0])

    # Write metric file.
    if uncovered_count is None:
        uncovered_count = 0
    metrics_str = f"Number of PII Annotation violations: {uncovered_count}\n"
    _write_metric(metrics_str, (Env.METRICS_DIR / pii_report_name))

    # Finally, fail the paver task if code_annotations suggests that the check failed.
    if not pii_check_passed:
        fail_quality('pii', full_log)


@task
@needs('pavelib.prereqs.install_python_prereqs')
@timed
def check_keywords():
    """
    Check Django model fields for names that conflict with a list of reserved keywords
    """
    report_path = os.path.join(Env.REPORT_DIR, 'reserved_keywords')
    sh(f"mkdir -p {report_path}")

    overall_status = True
    for env, env_settings_file in [('lms', 'lms.envs.test'), ('cms', 'cms.envs.test')]:
        report_file = f"{env}_reserved_keyword_report.csv"
        override_file = os.path.join(Env.REPO_ROOT, "db_keyword_overrides.yml")
        try:
            sh(
                "export DJANGO_SETTINGS_MODULE={settings_file}; "
                "python manage.py {app} check_reserved_keywords "
                "--override_file {override_file} "
                "--report_path {report_path} "
                "--report_file {report_file}".format(
                    settings_file=env_settings_file, app=env, override_file=override_file,
                    report_path=report_path, report_file=report_file
                )
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
<<<<<<< HEAD


@task
@needs('pavelib.prereqs.install_python_prereqs')
@timed
# pylint: disable=too-many-statements
def run_quality():
    """
    Build the html quality reports, and print the reports to the console.
    """
    failure_reasons = []

    def _lint_output(linter, count, violations_list, is_html=False):
        """
        Given a count & list of pylint violations, pretty-print the output.
        If `is_html`, will print out with HTML markup.
        """
        if is_html:
            lines = ['<body>\n']
            sep = '-------------<br/>\n'
            title = HTML("<h1>Quality Report: {}</h1>\n").format(linter)
            violations_bullets = ''.join(
                [HTML('<li>{violation}</li><br/>\n').format(violation=violation) for violation in violations_list]
            )
            violations_str = HTML('<ul>\n{bullets}</ul>\n').format(bullets=HTML(violations_bullets))
            violations_count_str = HTML("<b>Violations</b>: {count}<br/>\n")
            fail_line = HTML("<b>FAILURE</b>: {} count should be 0<br/>\n").format(linter)
        else:
            lines = []
            sep = '-------------\n'
            title = f"Quality Report: {linter}\n"
            violations_str = ''.join(violations_list)
            violations_count_str = "Violations: {count}\n"
            fail_line = f"FAILURE: {linter} count should be 0\n"

        violations_count_str = violations_count_str.format(count=count)

        lines.extend([sep, title, sep, violations_str, sep, violations_count_str])

        if count > 0:
            lines.append(fail_line)
        lines.append(sep + '\n')
        if is_html:
            lines.append('</body>')

        return ''.join(lines)

    (count, violations_list) = _get_pylint_violations(clean=False)

    # Print total number of violations to log
    print(_lint_output('pylint', count, violations_list))
    if count > 0:
        failure_reasons.append('Too many total pylint violations.')
        msg = "FAILURE: " + " ".join(failure_reasons)
        fail_quality('Quality Failure', msg)


def get_violations_reports(violations_type):
    """
    Finds violations reports files by naming convention (e.g., all "pep8.report" files)
    """
    violations_files = []
    for subdir, _dirs, files in os.walk(os.path.join(Env.REPORT_DIR)):
        for f in files:
            if f == f"{violations_type}.report":
                violations_files.append(os.path.join(subdir, f))
    return violations_files
=======
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

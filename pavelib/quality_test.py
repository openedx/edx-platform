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


class BuildFailure(Exception):
    """Represents a problem with some part of the build's execution."""
    pass


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


def run_eslint():
    """
    Runs eslint on static asset directories.
    If limit option is passed, fails build if more violations than the limit are found.
    """

    eslint_report_dir = (Env.REPORT_DIR / "eslint")
    eslint_report = eslint_report_dir / "eslint.report"
    _prepare_report_dir(eslint_report_dir)
    violations_limit = 4950

    command = (
        f"node --max_old_space_size=4096 node_modules/.bin/eslint "
        "--ext .js --ext .jsx --format=compact ."
    )
    with open(eslint_report, 'w') as report_file:
        # Run the command
        result = subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Write the output to the report file
        report_file.write(result.stdout)

    # Check the return code and handle errors if any
    if result.returncode != 0:
        print(f"Warning: eslint command exited with non-zero status {result.returncode}")

    # sh(
    #     "node --max_old_space_size=4096 node_modules/.bin/eslint "
    #     "--ext .js --ext .jsx --format=compact . | tee {eslint_report}".format(
    #         eslint_report=eslint_report
    #     ),
    #     ignore_error=True
    # )

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


def run_pii_check():
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
            os.makedirs(report_dir, exist_ok=True)
            command = (
                f"export DJANGO_SETTINGS_MODULE={env_settings_file}; "
                "code_annotations django_find_annotations "
                f"--config_file .pii_annotations.yml --report_path {report_dir} --app_name {env_name.lower()} "
                f"--lint --report --coverage | tee {run_output_file}"
            )
            # sh(
            #     "mkdir -p {} && "  # lint-amnesty, pylint: disable=duplicate-string-formatting-argument
            #     "export DJANGO_SETTINGS_MODULE={}; "
            #     "code_annotations django_find_annotations "
            #     "--config_file .pii_annotations.yml --report_path {} --app_name {} "
            #     "--lint --report --coverage | tee {}".format(
            #         report_dir, env_settings_file, report_dir, env_name.lower(), run_output_file
            #     )
            # )
            result = subprocess.run(command, shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            with open(run_output_file, 'w') as f:
                f.write(result.stdout)
            if result.returncode != 0:
                print(f"Warning: Command exited with non-zero status {result.returncode}")

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


if __name__ == "__main__":
    run_pep8()
    run_eslint()
    run_stylelint()
    run_pii_check()

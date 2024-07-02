# run_quality_checks.py

import os
import subprocess

def _get_pep8_violations(clean=True):
    """
    Runs pycodestyle. Returns a tuple of (number_of_violations, violations_string)
    where violations_string is a string of all PEP 8 violations found, separated
    by new lines.
    """
    # report_dir = REPORT_DIR / 'pep8'
    # if clean:
    #     report_dir.rmtree(ignore_errors=True)
    # report_dir.makedirs_p()
    # report = report_dir / 'pep8.report'

    # Make sure the metrics subdirectory exists
    # METRICS_DIR.makedirs_p()

    # if not report.exists():
        # sh(f'pycodestyle . | tee {report} -a')
        subprocess.run(['pycodestyle', '.']

    # violations_list = _pep8_violations(report)

    #return len(violations_list), violations_list


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
    _get_pep8_violations()
    # (count, violations_list) = _get_pep8_violations()
    # violations_list = ''.join(violations_list)

    # # Print number of violations to log
    # violations_count_str = f"Number of PEP 8 violations: {count}"
    # print(violations_count_str)
    # print(violations_list)

    # # Also write the number of violations to a file
    # with open(METRICS_DIR / "pep8", "w") as f:
    #     f.write(violations_count_str + '\n\n')
    #     f.write(violations_list)

    # # Fail if any violations are found
    # if count:
    #     failure_string = "FAILURE: Too many PEP 8 violations. " + violations_count_str
    #     failure_string += f"\n\nViolations:\n{violations_list}"
    #     fail_quality('pep8', failure_string)
    # else:
    #     write_junit_xml('pep8')


if __name__ == "__main__":
    run_pep8()

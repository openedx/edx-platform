"""
This script can be used to find the fewest number of tests required to get a
failure, in cases where a test failure is dependent on test order.

The script performs the following:
1. It strips the console log of a pytest-xdist Jenkins run into the test
lists of each pytest worker until it finds the first failure.
2. It makes sure that running the single failing test doesn't fail on its
own.
3. It then finds the fewest number of tests required to continue to see the
failure, and outputs the pytest command needed to replicate.

Sample usage::

    python scripts/xdist/find_dependent_test_failures.py --log-file console.txt --test-suite lms-unit

"""


import io
import os
import re
import shutil
import tempfile

import click

OUTPUT_FOLDER_NAME = "worker_list_files"
test_suite_option = None
fast_option = None
verbose_option = None


@click.command()
@click.option(
    '--log-file',
    help="File name of console log .txt file from a Jenkins build "
    "that ran pytest-xdist. This can be acquired by running: "
    "curl -o console.txt https://build.testeng.edx.org/job/JOBNAME/BUILDNUMBER/consoleText",
    required=True
)
@click.option(
    '--test-suite',
    help="Test suite that the pytest worker ran.",
    type=click.Choice(['lms-unit', 'cms-unit', 'commonlib-unit']),
    required=True
)
@click.option(
    '--fast/--slow',
    help="Fast looks for issues in setup/teardown by running one test per class or file.",
    default=True
)
@click.option(
    '--verbose/--quiet',
    help="Verbose includes the test output.",
    default=None
)
def main(log_file, test_suite, fast, verbose):
    global test_suite_option
    global fast_option
    global verbose_option
    test_suite_option = test_suite
    fast_option = fast
    verbose_option = verbose

    _clean_output_folder()

    failing_test_list = _strip_console_for_tests_with_failure(log_file, test_suite)

    if not failing_test_list:
        print('No failures found in log file.')
        return

    if _create_and_check_test_files_for_failures(failing_test_list[-1:], 'SINGLE'):
        print("Single test failed. Failures not dependent on order.")
        return

    test_list_with_failures, pytest_command = _find_fewest_tests_with_failures(failing_test_list, 'ALL')
    if test_list_with_failures:
        print('Found failures running {} tests.'.format(len(test_list_with_failures)))
        print('Use: {}'.format(pytest_command))
        return

    if fast_option:
        print('No tests failed locally with --fast option. Try running again with --slow to include more tests.')
        return

    print('No tests failed locally.')


def _clean_output_folder():
    if os.path.isdir(OUTPUT_FOLDER_NAME):
        shutil.rmtree(OUTPUT_FOLDER_NAME)
    os.mkdir(OUTPUT_FOLDER_NAME)


def _strip_console_for_tests_with_failure(log_file, test_suite):
    """
    Returns list of tests ending with a failing test, or None if no failures found.
    """
    global fast_option
    worker_test_dict = {}
    test_base_included = {}
    failing_worker_num = None
    with io.open(log_file, 'r') as console_file:
        for line in console_file:
            regex_search = re.search(r'\[gw(\d+)] (PASSED|FAILED|SKIPPED|ERROR) (\S+)'.format(test_suite), line)
            if regex_search:
                worker_num_string = regex_search.group(1)
                pass_fail_string = regex_search.group(2)
                if worker_num_string not in worker_test_dict:
                    worker_test_dict[worker_num_string] = []
                test = regex_search.group(3)
                if test_suite == "commonlib-unit":
                    if "pavelib" not in test and not test.startswith('scripts'):
                        test = u"common/lib/{}".format(test)
                if fast_option and pass_fail_string == 'PASSED':
                    # fast option will only take one test per class or module, in case
                    # the failure is a setup/teardown failure.
                    test_base = '::'.join(test.split('::')[:-1])
                    if test_base not in test_base_included:
                        worker_test_dict[worker_num_string].append(test)
                        test_base_included[test_base] = True
                elif (not fast_option or (fast_option and pass_fail_string == 'FAILED')):
                    worker_test_dict[worker_num_string].append(test)
                if pass_fail_string == 'FAILED':
                    failing_worker_num = worker_num_string
                    break
    if failing_worker_num:
        return worker_test_dict[failing_worker_num]


def _get_pytest_command(output_file_name):
    """
    Return the pytest command to run.
    """
    return "pytest -p 'no:randomly' `cat {}`".format(output_file_name)


def _run_tests_and_check_for_failures(output_file_name):
    """
    Runs tests and returns True if failures are found.
    """
    global verbose_option
    pytest_command = _get_pytest_command(output_file_name)
    test_output = os.popen(pytest_command).read()
    if verbose_option:
        print(test_output)
    failures_search = re.search(r'=== (\d+) failed', test_output)
    return bool(failures_search) and int(failures_search.group(1)) > 0


def _create_and_check_test_files_for_failures(test_list, test_type):
    """
    Run the test list to see if there are any failures.

    Keeps around any test files that produced a failure, and deletes
    the passing files.

    Returns the pytest command to run if failures are found.
    """
    print("Testing {}, includes {} test(s)...".format(test_type, len(test_list)))
    global test_suite_option
    output_file_name = "{}_failing_test_list_{}_{}.txt".format(
        OUTPUT_FOLDER_NAME, test_suite_option, test_type, len(test_list)
    )
    output_file_path = os.path.join(OUTPUT_FOLDER_NAME, output_file_name)
    # Note: We don't really need a temporary file, and could just output the tests directly
    # to the command line, but this keeps the verbose  output cleaner.
    temp_file = tempfile.NamedTemporaryFile(prefix=output_file_name, dir=OUTPUT_FOLDER_NAME, delete=False)

    with io.open(temp_file.name, 'w') as output_file:
        for line in test_list:
            output_file.write(line + "\n")
    temp_file.close()

    if _run_tests_and_check_for_failures(temp_file.name):
        os.rename(temp_file.name, output_file_path)
        print('- test failures found.')
        return _get_pytest_command(output_file_path)

    os.remove(temp_file.name)
    print('- no failures found.')
    return None


def _find_fewest_tests_with_failures(test_list, test_type):
    """
    Recursively tests half the tests, finding the smallest number of tests to obtain a failure.

    Returns:
        (test_list, pytest_command): Tuple with the smallest test_list and the pytest_command
            to be used for testing. Returns (None, None) if no failures are found.
    """
    if len(test_list) <= 1:
        return None, None

    pytest_command = _create_and_check_test_files_for_failures(test_list, test_type)
    if not pytest_command:
        return None, None

    if len(test_list) == 2:
        return test_list, pytest_command

    half_tests_num = round((len(test_list) - 1) / 2)
    failing_test = test_list[-1:]
    test_list_a = test_list[0:half_tests_num] + failing_test
    test_list_b = test_list[half_tests_num:]
    failing_test_list_a, pytest_command_a = _find_fewest_tests_with_failures(test_list_a, 'GROUP-A')
    if failing_test_list_a:
        return failing_test_list_a, pytest_command_a

    failing_test_list_b, pytest_command_b = _find_fewest_tests_with_failures(test_list_b, 'GROUP-B')
    if failing_test_list_b:
        return failing_test_list_b, pytest_command_b

    # This could occur if there is a complex set of dependencies where the
    # original list fails, but neither of its halves (A or B) fail.
    return test_list, pytest_command


if __name__ == "__main__":
    main()

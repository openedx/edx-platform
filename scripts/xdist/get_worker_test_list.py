"""
This script strips the console log of a pytest-xdist Jenkins run into the test
lists of each pytest worker.
Assumes the following format:
[test-suite] [worker] RESULT test
"""


import io
import os
import re
import shutil

import click


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
def main(log_file, test_suite):
    worker_test_dict = {}
    with io.open(log_file, 'r') as console_file:
        for line in console_file:
            regex_search = re.search(r'\[gw(\d+)] (PASSED|FAILED|SKIPPED|ERROR) (\S+)'.format(test_suite), line)
            if regex_search:
                worker_num_string = regex_search.group(1)
                if worker_num_string not in worker_test_dict:
                    worker_test_dict[worker_num_string] = []
                test = regex_search.group(3)
                if test_suite == "commonlib-unit":
                    if "pavelib" not in test and not test.startswith('scripts'):
                        test = u"common/lib/{}".format(test)
                worker_test_dict[worker_num_string].append(test)

    output_folder_name = "worker_list_files"
    if os.path.isdir(output_folder_name):
        shutil.rmtree(output_folder_name)
    os.mkdir(output_folder_name)

    for worker_num in worker_test_dict:
        output_file_name = "{}/{}_gw{}_test_list.txt".format(output_folder_name, test_suite, worker_num)
        with io.open(output_file_name, 'w') as output_file:
            for line in worker_test_dict[worker_num]:
                output_file.write(line + "\n")


if __name__ == "__main__":
    main()

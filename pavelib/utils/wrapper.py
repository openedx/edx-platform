from __future__ import print_function
import os
import re

from pavelib.utils.cmd import shell
from pavelib.utils.envs import Env

PACKAGE_DIRECTORIES = [
    'lib',
]


def pep8(services=None):
    services = services or []
    services = ' '.join(services)
    Env.METRICS_DIR.makedirs_p()
    report_dir = get_clean_report_directory('pep8')
    report_file = "{report_dir}/pep8.txt".format(
        report_dir=report_dir,
    )
    shell(
        'pep8',
        services,
        '|',
        'tee',
        report_file,
    )
    count = sum(1 for line in open(report_file))
    message_count = "Number of PEP8 violations: {count}".format(count=count)
    print(message_count)
    with open(Env.METRICS_DIR / 'pep8', 'w') as file_out:
        file_out.write(message_count)


def pylint(name, services, *flags):
    Env.METRICS_DIR.makedirs_p()
    count = 0
    for service in services:
        modules = _get_modules(service)
        environment = get_python_path(service)
        directory = get_clean_report_directory(service)
        report = "{directory}/{name}.txt".format(
            directory=directory,
            name=name,
        )
        shell(
            environment,
            'pylint',
            '--msg-template',
            "'{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}'",
            ' '.join(flags),
            modules,
            '|',
            'tee',
            report,
        )
        count += _count_pylint_violations(report)
    message = "Number of {name} violations: {count}".format(
        name=name,
        count=count,
    )
    print(message)
    with open(Env.METRICS_DIR / 'pylint', 'w') as file_out:
        file_out.write(message)
    return count


def get_clean_report_directory(service):
    """
    Directory to put the Pylint report in.

    This makes the folder if it doesn't already exist.
    """
    directory = Env.REPORT_DIR / service
    directory = directory.makedirs_p()
    return directory


def _count_pylint_violations(path_file_report):
    """
    Parses a pylint report line-by-line and determines the number of violations reported

    An example string:
    common/lib/xmodule/xmodule/tests/test_conditional.py:21:
        [C0111(missing-docstring), DummySystem] Missing docstring
    """
    count = 0
    pattern = re.compile(r'.(\d+):\ \[(\D\d+.+\]).')

    for line in open(path_file_report):
        parts = pattern.split(line)
        if len(parts) == 4:
            count += 1
    return count


def _get_modules(service, directories=None):
    directories = directories or PACKAGE_DIRECTORIES
    applications = [
        service,
    ]

    for directory in directories:
        try:
            directory_path = os.path.join(service, directory)
            subdirectories = os.listdir(directory_path)
        except OSError:
            continue
        applications.extend([
            application
            for application in subdirectories
            if os.path.isdir(os.path.join(service, directory, application))
        ])

    applications = ' '.join(applications)
    return applications


def get_pylint_reports():
    """
    Find Pylint violations reports files
    """
    reports = []
    path = os.path.join(Env.REPORT_DIR)
    for directory, _directories, files in os.walk(path):
        for report in files:
            if report == 'pylint.txt':
                report = os.path.join(directory, report)
                reports.append(report)
    return reports


def get_python_path(*services):
    paths = [
        '${PYTHONPATH}',
        'common/lib',
        'common/djangoapps',
    ]
    for service in services:
        paths.extend([
            service,
            os.path.join(service, 'lib'),
            os.path.join(service, 'djangoapps'),
        ])
    path = ':'.join(paths)
    path = 'PYTHONPATH=' + path
    return path

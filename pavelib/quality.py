"""
Check code quality using pep8, pylint, and diff_quality.
"""
from paver.easy import sh, task, cmdopts, needs
import os
import errno
from .utils.envs import Env

@task
@needs('pavelib.prereqs.install_python_prereqs')
@cmdopts([
    ("system=", "s", "System to act on"),
    ("errors", "e", "Check for errors only"),
])
def run_pylint(options):
    """
    Run pylint on system code
    """
    errors = getattr(options, 'errors', False)
    systems = getattr(options, 'system', 'lms,cms,common').split(',')

    for system in systems:
        # Directory to put the pylint report in.
        # This makes the folder if it doesn't already exist.
        report_dir = (Env.REPORT_DIR / system).makedirs_p()

        flags = '-E' if errors else ''

        apps = [system]

        for directory in ['djangoapps', 'lib']:
            dirs = os.listdir(os.path.join(system, directory))
            apps.extend([d for d in dirs if os.path.isdir(os.path.join(system, directory, d))])

        apps_list = ' '.join(apps)

        pythonpath_prefix = (
            "PYTHONPATH={system}:{system}/djangoapps:{system}/"
            "lib:common/djangoapps:common/lib".format(
                system=system
            )
        )

        sh(
            "{pythonpath_prefix} pylint {flags} -f parseable {apps} | "
            "tee {report_dir}/pylint.report".format(
                pythonpath_prefix=pythonpath_prefix,
                flags=flags,
                apps=apps_list,
                report_dir=report_dir
            )
        )


@task
@needs('pavelib.prereqs.install_python_prereqs')
@cmdopts([
    ("system=", "s", "System to act on"),
])
def run_pep8(options):
    """
    Run pep8 on system code
    """
    systems = getattr(options, 'system', 'lms,cms,common').split(',')

    for system in systems:
        # Directory to put the pep8 report in.
        # This makes the folder if it doesn't already exist.
        report_dir = (Env.REPORT_DIR / system).makedirs_p()

        sh('pep8 {system} | tee {report_dir}/pep8.report'.format(system=system, report_dir=report_dir))


@task
@needs('pavelib.prereqs.install_python_prereqs')
def run_quality():
    """
    Build the html diff quality reports, and print the reports to the console.
    """

    # Directory to put the diff reports in.
    # This makes the folder if it doesn't already exist.
    dquality_dir = (Env.REPORT_DIR / "diff_quality").makedirs_p()

    # Generage diff-quality html report for pep8, and print to console
    # If pep8 reports exist, use those
    # Otherwise, `diff-quality` will call pep8 itself

    pep8_files = []
    for subdir, _dirs, files in os.walk(os.path.join(Env.REPORT_DIR)):
        for f in files:
            if f == "pep8.report":
                pep8_files.append(os.path.join(subdir, f))

    pep8_reports = u' '.join(pep8_files)

    sh(
        "diff-quality --violations=pep8 --html-report {dquality_dir}/"
        "diff_quality_pep8.html {pep8_reports}".format(
            dquality_dir=dquality_dir, pep8_reports=pep8_reports)
    )

    sh(
        "diff-quality --violations=pep8 {pep8_reports}".format(
            pep8_reports=pep8_reports)
    )

    # Generage diff-quality html report for pylint, and print to console
    # If pylint reports exist, use those
    # Otherwise, `diff-quality` will call pylint itself

    pylint_files = []
    for subdir, _dirs, files in os.walk(os.path.join(Env.REPORT_DIR)):
        for f in files:
            if f == "pylint.report":
                pylint_files.append(os.path.join(subdir, f))

    pylint_reports = u' '.join(pylint_files)

    pythonpath_prefix = (
        "PYTHONPATH=$PYTHONPATH:lms:lms/djangoapps:lms/lib:cms:cms/djangoapps:cms/lib:"
        "common:common/djangoapps:common/lib"
    )

    sh(
        "{pythonpath_prefix} diff-quality --violations=pylint --html-report "
        "{dquality_dir}/diff_quality_pylint.html {pylint_reports}".format(
            pythonpath_prefix=pythonpath_prefix,
            dquality_dir=dquality_dir,
            pylint_reports=pylint_reports
        )
    )

    sh(
        "{pythonpath_prefix} diff-quality --violations=pylint {pylint_reports}".format(
            pythonpath_prefix=pythonpath_prefix,
            pylint_reports=pylint_reports
        )
    )

from paver.easy import *
from pavelib import assets, prereqs
import os


@task
@cmdopts([
    ("system=", "s", "System to act on"),
    ("errors", "e", "Check for errors only"),
])
def run_pylint(options):
    """
    Run pylint checking for {system} if --errors specified check for errors only, and abort if there are any
    """
    system = getattr(options, 'system', 'lms')
    errors = getattr(options, 'errors', False)

    report_dir = os.path.join(assets.REPORT_DIR, system)

    flags = '-E' if errors else ''

    prereqs.install_python_prereqs()

    apps = [system]

    dirs = os.listdir(os.path.join(system, 'djangoapps'))
    for dir in dirs:
        if not dir.endswith('.pyc'):
            apps.append(dir)

    if not system == 'lms':
        dirs = os.listdir(os.path.join(system, 'lib'))
        for dir in dirs:
            if not dir.endswith('.pyc'):
                apps.append(dir)

    apps_list = ' '.join(apps)

    pythonpath_prefix = "PYTHONPATH={system}:{system}/djangoapps:{system}/lib:common/djangoapps:common/lib".format(
                        system=system)
    sh("{pythonpath_prefix} pylint {flags} -f parseable {apps} | tee {report_dir}/pylint.report".format(
        pythonpath_prefix=pythonpath_prefix, flags=flags, apps=apps_list, report_dir=report_dir)
       )


@task
@cmdopts([
    ("system=", "s", "System to act on"),
])
def run_pep8(options):
    """
    Run pep8 on system code
    """
    system = getattr(options, 'system', 'lms')

    report_dir = os.path.join(assets.REPORT_DIR, system)

    prereqs.install_python_prereqs()
    sh('pep8 {system} | tee {report_dir}/pep8.report'.format(system=system, report_dir=report_dir))


@task
@cmdopts([
    ("quality_dir=", "s", "System to act on"),
])
def run_quality(options):
    """
    Build the html diff quality reports, and print the reports to the console.
    """

    dquality_dir = os.path.join(assets.REPORT_DIR, "diff_quality")

    # Generage diff-quality html report for pep8, and print to console
    # If pep8 reports exist, use those
    # Otherwise, `diff-quality` will call pep8 itself

    pep8_files = []

    for subdir, dirs, files in os.walk(os.path.join(assets.REPORT_DIR)):
        for file in files:
            if file == "pep8.report":
                pep8_files.append(os.path.join(subdir, file))

    pep8_reports = ' '.join(pep8_files)
    sh("diff-quality --violations=pep8 --html-report {dquality_dir}/diff_quality_pep8.html {pep8_reports}".format(
        dquality_dir=dquality_dir, pep8_reports=pep8_reports))
    sh("diff-quality --violations=pep8 {pep8_reports}".format(pep8_reports=pep8_reports))

    # Generage diff-quality html report for pylint, and print to console
    # If pylint reports exist, use those
    # Otherwise, `diff-quality` will call pylint itself

    pylint_files = []
    for subdir, dirs, files in os.walk(os.path.join(assets.REPORT_DIR)):
        for file in files:
            if file == "pylint.report":
                pylint_files.append(os.path.join(subdir, file))

    pylint_reports = ' '.join(pylint_files)
    pythonpath_prefix = "PYTHONPATH=$PYTHONPATH:lms:lms/djangoapps:lms/lib:cms:cms/djangoapps:cms/lib:common:common/djangoapps:common/lib"
    sh("{pythonpath_prefix} diff-quality --violations=pylint --html-report {dquality_dir}/diff_quality_pylint.html {pylint_reports}".format(
        pythonpath_prefix=pythonpath_prefix, dquality_dir=dquality_dir, pylint_reports=pylint_reports))
    sh("{pythonpath_prefix} diff-quality --violations=pylint {pylint_reports}".format(
        pythonpath_prefix=pythonpath_prefix, pylint_reports=pylint_reports))

from paver.easy import *
from pavelib import assets, test_utils, prereqs

import os
import errno

__test__ = False  # do not collect

ACCEPTANCE_DB = 'test_root/db/test_edx.db'
ACCEPTANCE_REPORT_DIR = os.path.join(assets.REPORT_DIR, 'acceptance')


def run_acceptance_tests(system, harvest_args):
    # Create the acceptance report directory
    # because if it doesn't exist then lettuce will give an IOError.

    try:
        os.makedirs(ACCEPTANCE_REPORT_DIR)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

    report_file = os.path.join(ACCEPTANCE_REPORT_DIR, '{system}.xml'.format(system=system))
    report_args = '--with-xunit --xunit-file {report_file}'.format(report_file=report_file)

    cmd = ('python manage.py {system} harvest --traceback --settings=acceptance --pythonpath=. '
           '--debug-mode --verbosity 2 {report_args} {harvest_args} '.format(
           system=system, report_args=report_args, harvest_args=harvest_args))

    test_utils.test_sh(cmd)


def setup_acceptance_db():
    # HACK: Since the CMS depends on the existence of some database tables
    # that are now in common but used to be in LMS (Role/Permissions for Forums)
    # we need to create/migrate the database tables defined in the LMS.
    # We might be able to address this by moving out the migrations from
    # lms/django_comment_client, but then we'd have to repair all the existing
    # migrations from the upgrade tables in the DB.
    # But for now for either system (lms or cms), use the lms
    # definitions to sync and migrate.

    if os.path.isfile(ACCEPTANCE_DB):
        os.remove(ACCEPTANCE_DB)

    sh('python manage.py lms syncdb --noinput --settings=acceptance --pythonpath=.')
    sh('python manage.py lms migrate --noinput --settings=acceptance --pythonpath=.')


def prep_for_acceptance_tests(init_db=True):
    test_utils.clean_dir(ACCEPTANCE_REPORT_DIR)
    test_utils.clean_test_files()
    prereqs.install_prereqs()
    if init_db:
        setup_acceptance_db()


@task
@cmdopts([
    ("harvest_args=", "", "Arguments to pass for harvest"),
])
def test_acceptance_all(options):
    """
    Run acceptance tests on all systems
    """
    setattr(options, 'system', 'cms')
    test_acceptance(options)
    setattr(options, 'system', 'lms')
    test_acceptance(options)


@task
@cmdopts([
    ("system=", "s", "System to act on"),
    ("harvest_args=", "", "Arguments to pass for harvest"),
])
def test_acceptance(options):
    """
    Run acceptance tests on system specified
    """

    system = getattr(options, 'system', 'lms')
    harvest_args = getattr(options, 'harvest_args', '')

    prep_for_acceptance_tests()

    setattr(options, 'system', 'cms')
    setattr(options, 'env', 'acceptance')
    setattr(options, 'collectstatic', True)
    assets.compile_assets(options)

    setattr(options, 'system', 'lms')
    assets.compile_assets(options)

    run_acceptance_tests(system, harvest_args)


@task
@cmdopts([
    ("system=", "s", "System to act on"),
    ("harvest_args=", "", "Arguments to pass for harvest"),
])
def test_acceptance_fast(options):
    '''
    Run acceptance tests withouth collectstatic and without init db
    '''

    system = getattr(options, 'system', 'lms')
    harvest_args = getattr(options, 'harvest_args', '')

    prep_for_acceptance_tests(False)

    setattr(options, 'system', 'cms')
    setattr(options, 'env', 'acceptance')
    assets.compile_assets(options)

    setattr(options, 'system', 'lms')
    assets.compile_assets(options)

    run_acceptance_tests(system, harvest_args)

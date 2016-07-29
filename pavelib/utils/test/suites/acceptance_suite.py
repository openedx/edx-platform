"""
Acceptance test suite
"""
from paver.easy import sh, call_task, task
from pavelib.utils.test import utils as test_utils
from pavelib.utils.test.suites.suite import TestSuite
from pavelib.utils.envs import Env
from pavelib.utils.timer import timed

__test__ = False  # do not collect


DBS = {
    'default': Env.REPO_ROOT / 'test_root/db/test_edx.db',
    'student_module_history': Env.REPO_ROOT / 'test_root/db/test_student_module_history.db'
}
DB_CACHES = {
    'default': Env.REPO_ROOT / 'common/test/db_cache/lettuce.db',
    'student_module_history': Env.REPO_ROOT / 'common/test/db_cache/lettuce_student_module_history.db'
}


@task
@timed
def setup_acceptance_db():
    """
    TODO: Improve the following

    Since the CMS depends on the existence of some database tables
    that are now in common but used to be in LMS (Role/Permissions for Forums)
    we need to create/migrate the database tables defined in the LMS.
    We might be able to address this by moving out the migrations from
    lms/django_comment_client, but then we'd have to repair all the existing
    migrations from the upgrade tables in the DB.
    But for now for either system (lms or cms), use the lms
    definitions to sync and migrate.
    """

    for db in DBS.keys():
        if DBS[db].isfile():
            # Since we are using SQLLite, we can reset the database by deleting it on disk.
            DBS[db].remove()

    if all(DB_CACHES[cache].isfile() for cache in DB_CACHES.keys()):
        # To speed up migrations, we check for a cached database file and start from that.
        # The cached database file should be checked into the repo

        # Copy the cached database to the test root directory
        for db_alias in DBS.keys():
            sh("cp {db_cache} {db}".format(db_cache=DB_CACHES[db_alias], db=DBS[db_alias]))

        # Run migrations to update the db, starting from its cached state
        for db_alias in sorted(DBS.keys()):
            # pylint: disable=line-too-long
            sh("./manage.py lms --settings acceptance migrate --traceback --noinput --fake-initial --database {}".format(db_alias))
            sh("./manage.py cms --settings acceptance migrate --traceback --noinput --fake-initial --database {}".format(db_alias))
    else:
        # If no cached database exists, syncdb before migrating, then create the cache
        for db_alias in sorted(DBS.keys()):
            sh("./manage.py lms --settings acceptance migrate --traceback --noinput --database {}".format(db_alias))
            sh("./manage.py cms --settings acceptance migrate --traceback --noinput --database {}".format(db_alias))

        # Create the cache if it doesn't already exist
        for db_alias in DBS.keys():
            sh("cp {db} {db_cache}".format(db_cache=DB_CACHES[db_alias], db=DBS[db_alias]))


class AcceptanceTest(TestSuite):
    """
    A class for running lettuce acceptance tests.
    """
    def __init__(self, *args, **kwargs):
        super(AcceptanceTest, self).__init__(*args, **kwargs)
        self.report_dir = Env.REPORT_DIR / 'acceptance'
        self.fasttest = kwargs.get('fasttest', False)
        self.system = kwargs.get('system')
        self.default_store = kwargs.get('default_store')
        self.extra_args = kwargs.get('extra_args', '')

    def __enter__(self):
        super(AcceptanceTest, self).__enter__()
        self.report_dir.makedirs_p()
        self._update_assets()

    def __exit__(self, exc_type, exc_value, traceback):
        super(AcceptanceTest, self).__exit__(exc_type, exc_value, traceback)
        test_utils.clean_mongo()

    @property
    def cmd(self):

        report_file = self.report_dir / "{}.xml".format(self.system)
        report_args = ["--xunit-file {}".format(report_file)]
        return [
            "DEFAULT_STORE={}".format(self.default_store),
            "./manage.py",
            self.system,
            "--settings=acceptance",
            "harvest",
            "--traceback",
            "--debug-mode",
            "--verbosity={}".format(self.verbosity),
        ] + report_args + [
            self.extra_args
        ] + self.passthrough_options

    def _update_assets(self):
        """
        Internal helper method to manage asset compilation
        """
        args = [self.system, '--settings=acceptance']

        if self.fasttest:
            args.append('--skip-collect')

        call_task('pavelib.assets.update_assets', args=args)


class AcceptanceTestSuite(TestSuite):
    """
    A class for running lettuce acceptance tests.
    """
    def __init__(self, *args, **kwargs):
        super(AcceptanceTestSuite, self).__init__(*args, **kwargs)
        self.root = 'acceptance'
        self.fasttest = kwargs.get('fasttest', False)

        if kwargs.get('system'):
            systems = [kwargs['system']]
        else:
            systems = ['lms', 'cms']

        if kwargs.get('default_store'):
            stores = [kwargs['default_store']]
        else:
            # TODO fix Acceptance tests with Split (LMS-11300)
            # stores = ['split', 'draft']
            stores = ['draft']

        self.subsuites = []
        for system in systems:
            for default_store in stores:
                kwargs['system'] = system
                kwargs['default_store'] = default_store
                self.subsuites.append(AcceptanceTest('{} acceptance using {}'.format(system, default_store), **kwargs))

    def __enter__(self):
        super(AcceptanceTestSuite, self).__enter__()
        if not (self.fasttest or self.skip_clean):
            test_utils.clean_test_files()

        if not self.fasttest:
            setup_acceptance_db()

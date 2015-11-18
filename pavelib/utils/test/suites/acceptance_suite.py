"""
Acceptance test suite
"""
from paver.easy import sh, call_task
from pavelib.utils.test import utils as test_utils
from pavelib.utils.test.suites.suite import TestSuite
from pavelib.utils.envs import Env

__test__ = False  # do not collect


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
        report_args = "--with-xunit --xunit-file {}".format(report_file)

        cmd = (
            "DEFAULT_STORE={default_store} ./manage.py {system} --settings acceptance harvest --traceback "
            "--debug-mode --verbosity {verbosity} {pdb}{report_args} {extra_args}".format(
                default_store=self.default_store,
                system=self.system,
                verbosity=self.verbosity,
                pdb="--pdb " if self.pdb else "",
                report_args=report_args,
                extra_args=self.extra_args,
            )
        )

        return cmd

    def _update_assets(self):
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
        self.db = Env.REPO_ROOT / 'test_root/db/test_edx.db'
        self.db_cache = Env.REPO_ROOT / 'common/test/db_cache/lettuce.db'
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
            self._setup_acceptance_db()

    def _setup_acceptance_db(self):
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

        if self.db.isfile():
            # Since we are using SQLLite, we can reset the database by deleting it on disk.
            self.db.remove()

        if self.db_cache.isfile():
            # To speed up migrations, we check for a cached database file and start from that.
            # The cached database file should be checked into the repo

            # Copy the cached database to the test root directory
            sh("cp {db_cache} {db}".format(db_cache=self.db_cache, db=self.db))

            # Run migrations to update the db, starting from its cached state
            sh("./manage.py lms --settings acceptance migrate --traceback --noinput")
            sh("./manage.py cms --settings acceptance migrate --traceback --noinput")
        else:
            # If no cached database exists, syncdb before migrating, then create the cache
            sh("./manage.py lms --settings acceptance syncdb --traceback --noinput")
            sh("./manage.py cms --settings acceptance syncdb --traceback --noinput")
            sh("./manage.py lms --settings acceptance migrate --traceback --noinput")
            sh("./manage.py cms --settings acceptance migrate --traceback --noinput")

            # Create the cache if it doesn't already exist
            sh("cp {db} {db_cache}".format(db_cache=self.db_cache, db=self.db))

from lettuce import before, after, world
from splinter.browser import Browser
from splinter.driver.webdriver.firefox import FirefoxProfile
from logging import getLogger
import time

logger = getLogger(__name__)
logger.info("Loading the terrain file...")

try:
    from django.core.management import call_command
    from django.conf import settings
    from django.test.simple import DjangoTestSuiteRunner
    from django.core import mail

    try:
        from south.management.commands import patch_for_test_db_setup
        USE_SOUTH = getattr(settings, "SOUTH_TESTS_MIGRATE", False)
    except:
        USE_SOUTH = False

    @before.runserver
    def setup_database(actual_server):
        logger.info("Setting up a test database...")

        if USE_SOUTH:
            patch_for_test_db_setup()

        world.test_runner = DjangoTestSuiteRunner(interactive=False)
        DjangoTestSuiteRunner.setup_test_environment(world.test_runner)
        world.created_db = DjangoTestSuiteRunner.setup_databases(world.test_runner)

        # call_command('syncdb', interactive=False, verbosity=0)
        # call_command('migrate', interactive=False, verbosity=0)

        # because the TestSuiteRunner setup_test_environment hard codes it to False
        settings.DEBUG = True 

    @after.runserver
    def teardown_database(actual_server):
        if hasattr(world, "test_runner"):
            logger.info("Destroying the test database ...")
            DjangoTestSuiteRunner.teardown_databases(world.test_runner, world.created_db)
            DjangoTestSuiteRunner.teardown_test_environment(world.test_runner)

    @before.harvest
    def initial_setup(server):
        # call_command('syncdb', interactive=False, verbosity=2)
        # call_command('migrate', interactive=False, verbosity=2)

        world.browser = Browser('firefox')
        # pass

        # logger.info('Sleeping 7 seconds to give the server time to compile the js...')
        # time.sleep(float(7))
        # logger.info('...done sleeping.')

    @before.each_scenario
    def reset_data(scenario):
        # Clean up django.
        logger.info("Flushing the test database...")
        call_command('flush', interactive=False)
        #call_command('loaddata', 'all', verbosity=0)

    @after.all
    def teardown_browser(total):
        # world.browser.driver.save_screenshot('/tmp/selenium_screenshot.png')
       # world.browser.quit()
       pass


except:
    try:
        # Only complain if it seems likely that using django was intended.
        import django
        logger.warn("Django terrains not imported.")
    except:
        pass    
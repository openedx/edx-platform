from lettuce import before, after, world
from splinter.browser import Browser
from logging import getLogger

# Let the LMS and CMS do their one-time setup
# For example, setting up mongo caches
from lms import one_time_startup
from cms import one_time_startup

logger = getLogger(__name__)
logger.info("Loading the lettuce acceptance testing terrain file...")

from django.core.management import call_command


@before.harvest
def initial_setup(server):
    '''
    Launch the browser once before executing the tests
    '''
    # Launch the browser app (choose one of these below)
    world.browser = Browser('chrome')
    # world.browser = Browser('phantomjs')
    # world.browser = Browser('firefox')


@before.each_scenario
def reset_data(scenario):
    '''
    Clean out the django test database defined in the
    envs/acceptance.py file: mitx_all/db/test_mitx.db
    '''
    logger.debug("Flushing the test database...")
    call_command('flush', interactive=False)


@after.all
def teardown_browser(total):
    '''
    Quit the browser after executing the tests
    '''
    world.browser.quit()
    pass

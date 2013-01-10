from lettuce import before, after, world
from splinter.browser import Browser
from logging import getLogger
import time

logger = getLogger(__name__)
logger.info("Loading the lettuce acceptance testing terrain file...")

from django.core.management import call_command

@before.harvest
def initial_setup(server):
    # Launch firefox
    world.browser = Browser('chrome')

@before.each_scenario
def reset_data(scenario):
    # Clean out the django test database defined in the 
    # envs/acceptance.py file: mitx_all/db/test_mitx.db
    logger.debug("Flushing the test database...")
    call_command('flush', interactive=False)

@after.all
def teardown_browser(total):
    # Quit firefox
    world.browser.quit()
    pass
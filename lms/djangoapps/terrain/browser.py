from lettuce import before, after, world
from splinter.browser import Browser
from logging import getLogger
import time

logger = getLogger(__name__)
logger.info("Loading the terrain file...")

from django.core.management import call_command

@before.harvest
def initial_setup(server):

    # Sync the test database defined in the settings.py file
    # then apply the SOUTH migrations
    call_command('syncdb', interactive=False)
    call_command('migrate', interactive=False)

    # Launch firefox
    world.browser = Browser('firefox')

@before.each_scenario
def reset_data(scenario):
    # Clean up the django database
    logger.info("Flushing the test database...")
    call_command('flush', interactive=False)

@after.all
def teardown_browser(total):
    # Quit firefox
    world.browser.quit()

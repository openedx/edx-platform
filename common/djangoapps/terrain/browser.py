from lettuce import before, after, world
from splinter.browser import Browser
from logging import getLogger
from django.core.management import call_command
from django.conf import settings

# Let the LMS and CMS do their one-time setup
# For example, setting up mongo caches
from lms import one_time_startup
from cms import one_time_startup

# There is an import issue when using django-staticfiles with lettuce
# Lettuce assumes that we are using django.contrib.staticfiles,
# but the rest of the app assumes we are using django-staticfiles
# (in particular, django-pipeline and our mako implementation)
# To resolve this, we check whether staticfiles is installed,
# then redirect imports for django.contrib.staticfiles
# to use staticfiles.
try:
    import staticfiles
except ImportError:
    pass
else:
    import sys
    sys.modules['django.contrib.staticfiles'] = staticfiles

logger = getLogger(__name__)
logger.info("Loading the lettuce acceptance testing terrain file...")


@before.harvest
def initial_setup(server):
    '''
    Launch the browser once before executing the tests
    '''
    browser_driver = getattr(settings, 'LETTUCE_BROWSER', 'chrome')
    world.browser = Browser(browser_driver)


@before.each_scenario
def reset_data(scenario):
    '''
    Clean out the django test database defined in the
    envs/acceptance.py file: mitx_all/db/test_mitx.db
    '''
    logger.debug("Flushing the test database...")
    call_command('flush', interactive=False)


@after.each_scenario
def screenshot_on_error(scenario):
    '''
    Save a screenshot to help with debugging
    '''
    if scenario.failed:
        world.browser.driver.save_screenshot('/tmp/last_failed_scenario.png')


@after.all
def teardown_browser(total):
    '''
    Quit the browser after executing the tests
    '''
    world.browser.quit()
    pass

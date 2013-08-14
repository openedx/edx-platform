"""
Browser set up for acceptance tests.
"""

#pylint: disable=E1101
#pylint: disable=W0613

from lettuce import before, after, world
from splinter.browser import Browser
from logging import getLogger
from django.core.management import call_command
from django.conf import settings
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

# Let the LMS and CMS do their one-time setup
# For example, setting up mongo caches
# These names aren't used, but do important work on import.
from lms import one_time_startup        # pylint: disable=W0611
from cms import one_time_startup        # pylint: disable=W0611
from pymongo import MongoClient
import xmodule.modulestore.django
from xmodule.contentstore.django import _CONTENTSTORE

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

LOGGER = getLogger(__name__)
LOGGER.info("Loading the lettuce acceptance testing terrain file...")

MAX_VALID_BROWSER_ATTEMPTS = 20

# https://gist.github.com/santiycr/1644439
import httplib
import base64
try:
    import json
except ImportError:
    import simplejson as json


SAUCE = settings.MITX_FEATURES.get('SAUCE', {})

config = {"username": SAUCE.get('USERNAME'),
"access-key": SAUCE.get('ACCESS_ID')}

desired_capabilities =  SAUCE.get('BROWSER', DesiredCapabilities.CHROME)
desired_capabilities['platform'] = SAUCE.get('PLATFORM', 'Linux')
desired_capabilities['version'] = SAUCE.get('VERSION', '')
desired_capabilities['device-type'] = SAUCE.get('DEVICE', '')
desired_capabilities['name'] = SAUCE.get('SESSION', 'Lettuce Tests')
desired_capabilities['build'] = SAUCE.get('BUILD', 'edX Plaform')
desired_capabilities['custom-data'] = SAUCE.get('CUSTOM_TAGS', '')
desired_capabilities['video-upload-on-pass'] = False
desired_capabilities['sauce-advisor'] = False
desired_capabilities['record-screenshots'] = False
desired_capabilities['selenium-version'] = "2.34.0"
desired_capabilities['max-duration'] = 3600
desired_capabilities['public'] = 'public restricted'
jobid=''

base64string = base64.encodestring('%s:%s' % (config['username'], config['access-key']))[:-1]

def set_job_status(jobid, passed=True):
    body_content = json.dumps({"passed": passed})
    connection = httplib.HTTPConnection("saucelabs.com")
    connection.request('PUT', '/rest/v1/%s/jobs/%s' % (config['username'], jobid),
    body_content,
    headers={"Authorization": "Basic %s" % base64string})
    result = connection.getresponse()
    return result.status == 200


@before.harvest
def initial_setup(server):
    """
    Launch the browser once before executing the tests.
    """
    browser_driver = getattr(settings, 'LETTUCE_BROWSER', 'chrome')

    # There is an issue with ChromeDriver2 r195627 on Ubuntu
    # in which we sometimes get an invalid browser session.
    # This is a work-around to ensure that we get a valid session.
    success = False
    num_attempts = 0
    while (not success) and num_attempts < MAX_VALID_BROWSER_ATTEMPTS:

        # Get a browser session
        if SAUCE.get('ENABLED'):
            world.browser = Browser(
                'remote',
                url="http://{}:{}@ondemand.saucelabs.com:80/wd/hub".format(config['username'],config['access-key']),
                **desired_capabilities
            )
            global jobid
            jobid = world.browser.driver.session_id
        else:
            world.browser = Browser(browser_driver)

        world.browser.driver.implicitly_wait(30)

        # Try to visit the main page
        # If the browser session is invalid, this will
        # raise a WebDriverException
        try:
            world.visit('/')

        except WebDriverException:
            world.browser.quit()
            num_attempts += 1

        else:
            success = True

    # If we were unable to get a valid session within the limit of attempts,
    # then we cannot run the tests.
    if not success:
        raise IOError("Could not acquire valid {driver} browser session.".format(driver='remote'))

    # Set the browser size to 1280x1024
    if not SAUCE.get('ENABLED'):
        world.browser.driver.set_window_size(1280, 1024)


@before.each_scenario
def reset_data(scenario):
    """
    Clean out the django test database defined in the
    envs/acceptance.py file: mitx_all/db/test_mitx.db
    """
    LOGGER.debug("Flushing the test database...")
    call_command('flush', interactive=False)
    world.absorb({}, 'scenario_dict')


@after.each_scenario
def clear_data(scenario):
    world.spew('scenario_dict')



@after.each_scenario
def reset_databases(scenario):
    '''
    After each scenario, all databases are cleared/dropped.  Contentstore data are stored in unique databases
    whereas modulestore data is in unique collection names.  This data is created implicitly during the scenarios.
    If no data is created during the test, these lines equivilently do nothing.
    '''
    mongo = MongoClient()
    mongo.drop_database(settings.CONTENTSTORE['OPTIONS']['db'])
    _CONTENTSTORE.clear()
    modulestore = xmodule.modulestore.django.modulestore()
    modulestore.collection.drop()
    xmodule.modulestore.django._MODULESTORES.clear()


# Uncomment below to trigger a screenshot on error
# @after.each_scenario
def screenshot_on_error(scenario):
    """
    Save a screenshot to help with debugging.
    """
    if scenario.failed:
        world.browser.driver.save_screenshot('/tmp/last_failed_scenario.png')


@after.all
def teardown_browser(total):
    """
    Quit the browser after executing the tests.
    """
    if SAUCE.get('ENABLED'):
            set_job_status(jobid, total.scenarios_ran == total.scenarios_passed)
    world.browser.quit()

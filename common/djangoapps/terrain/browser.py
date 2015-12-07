"""
Browser set up for acceptance tests.
"""

# pylint: disable=no-member
# pylint: disable=unused-argument

from lettuce import before, after, world
from splinter.browser import Browser
from logging import getLogger
from django.core.management import call_command
from django.conf import settings
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import requests
from base64 import encodestring
from json import dumps

import xmodule.modulestore.django
from xmodule.contentstore.django import _CONTENTSTORE

LOGGER = getLogger(__name__)
LOGGER.info("Loading the lettuce acceptance testing terrain file...")

MAX_VALID_BROWSER_ATTEMPTS = 20
GLOBAL_SCRIPT_TIMEOUT = 60


def get_saucelabs_username_and_key():
    """
    Returns the Sauce Labs username and access ID as set by environment variables
    """
    return {"username": settings.SAUCE.get('USERNAME'), "access-key": settings.SAUCE.get('ACCESS_ID')}


def set_saucelabs_job_status(jobid, passed=True):
    """
    Sets the job status on sauce labs
    """
    config = get_saucelabs_username_and_key()
    url = 'http://saucelabs.com/rest/v1/{}/jobs/{}'.format(config['username'], world.jobid)
    body_content = dumps({"passed": passed})
    base64string = encodestring('{}:{}'.format(config['username'], config['access-key']))[:-1]
    headers = {"Authorization": "Basic {}".format(base64string)}
    result = requests.put(url, data=body_content, headers=headers)
    return result.status_code == 200


def make_saucelabs_desired_capabilities():
    """
    Returns a DesiredCapabilities object corresponding to the environment sauce parameters
    """
    desired_capabilities = settings.SAUCE.get('BROWSER', DesiredCapabilities.CHROME)
    desired_capabilities['platform'] = settings.SAUCE.get('PLATFORM')
    desired_capabilities['version'] = settings.SAUCE.get('VERSION')
    desired_capabilities['device-type'] = settings.SAUCE.get('DEVICE')
    desired_capabilities['name'] = settings.SAUCE.get('SESSION')
    desired_capabilities['build'] = settings.SAUCE.get('BUILD')
    desired_capabilities['video-upload-on-pass'] = False
    desired_capabilities['sauce-advisor'] = False
    desired_capabilities['capture-html'] = True
    desired_capabilities['record-screenshots'] = True
    desired_capabilities['selenium-version'] = "2.34.0"
    desired_capabilities['max-duration'] = 3600
    desired_capabilities['public'] = 'public restricted'
    return desired_capabilities


@before.harvest
def initial_setup(server):
    """
    Launch the browser once before executing the tests.
    """
    world.absorb(settings.LETTUCE_SELENIUM_CLIENT, 'LETTUCE_SELENIUM_CLIENT')

    if world.LETTUCE_SELENIUM_CLIENT == 'local':
        browser_driver = getattr(settings, 'LETTUCE_BROWSER', 'chrome')

        if browser_driver == 'chrome':
            desired_capabilities = DesiredCapabilities.CHROME
            desired_capabilities['loggingPrefs'] = {
                'browser': 'ALL',
            }
        elif browser_driver == 'firefox':
            desired_capabilities = DesiredCapabilities.FIREFOX
        else:
            desired_capabilities = {}

        # There is an issue with ChromeDriver2 r195627 on Ubuntu
        # in which we sometimes get an invalid browser session.
        # This is a work-around to ensure that we get a valid session.
        success = False
        num_attempts = 0
        while (not success) and num_attempts < MAX_VALID_BROWSER_ATTEMPTS:

            # Load the browser and try to visit the main page
            # If the browser couldn't be reached or
            # the browser session is invalid, this will
            # raise a WebDriverException
            try:
                world.browser = Browser(browser_driver, desired_capabilities=desired_capabilities)
                world.browser.driver.set_script_timeout(GLOBAL_SCRIPT_TIMEOUT)
                world.visit('/')

            except WebDriverException:
                LOGGER.warn("Error acquiring %s browser, retrying", browser_driver, exc_info=True)
                if hasattr(world, 'browser'):
                    world.browser.quit()
                num_attempts += 1

            else:
                success = True

        # If we were unable to get a valid session within the limit of attempts,
        # then we cannot run the tests.
        if not success:
            raise IOError("Could not acquire valid {driver} browser session.".format(driver=browser_driver))

        world.absorb(0, 'IMPLICIT_WAIT')
        world.browser.driver.set_window_size(1280, 1024)

    elif world.LETTUCE_SELENIUM_CLIENT == 'saucelabs':
        config = get_saucelabs_username_and_key()
        world.browser = Browser(
            'remote',
            url="http://{}:{}@ondemand.saucelabs.com:80/wd/hub".format(config['username'], config['access-key']),
            **make_saucelabs_desired_capabilities()
        )
        world.absorb(30, 'IMPLICIT_WAIT')
        world.browser.set_script_timeout(GLOBAL_SCRIPT_TIMEOUT)

    elif world.LETTUCE_SELENIUM_CLIENT == 'grid':
        world.browser = Browser(
            'remote',
            url=settings.SELENIUM_GRID.get('URL'),
            browser=settings.SELENIUM_GRID.get('BROWSER'),
        )
        world.absorb(30, 'IMPLICIT_WAIT')
        world.browser.driver.set_script_timeout(GLOBAL_SCRIPT_TIMEOUT)

    else:
        raise Exception("Unknown selenium client '{}'".format(world.LETTUCE_SELENIUM_CLIENT))

    world.browser.driver.implicitly_wait(world.IMPLICIT_WAIT)
    world.absorb(world.browser.driver.session_id, 'jobid')


@before.each_scenario
def reset_data(scenario):
    """
    Clean out the django test database defined in the
    envs/acceptance.py file: edx-platform/db/test_edx.db
    """
    LOGGER.debug("Flushing the test database...")
    call_command('flush', interactive=False, verbosity=0)
    world.absorb({}, 'scenario_dict')


@before.each_scenario
def configure_screenshots(scenario):
    """
    Before each scenario, turn off automatic screenshots.

    Args: str, scenario. Name of current scenario.
    """
    world.auto_capture_screenshots = False


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
    xmodule.modulestore.django.modulestore()._drop_database()  # pylint: disable=protected-access
    xmodule.modulestore.django.clear_existing_modulestores()
    _CONTENTSTORE.clear()


@world.absorb
def capture_screenshot(image_name):
    """
    Capture a screenshot outputting it to a defined directory.
    This function expects only the name of the file. It will generate
    the full path of the output screenshot.

    If the name contains spaces, they ill be converted to underscores.
    """
    output_dir = '{}/log/auto_screenshots'.format(settings.TEST_ROOT)
    image_name = '{}/{}.png'.format(output_dir, image_name.replace(' ', '_'))
    try:
        world.browser.driver.save_screenshot(image_name)
    except WebDriverException:
        LOGGER.error("Could not capture a screenshot '{}'".format(image_name))


@after.each_scenario
def screenshot_on_error(scenario):
    """
    Save a screenshot to help with debugging.
    """
    if scenario.failed:
        try:
            output_dir = '{}/log'.format(settings.TEST_ROOT)
            image_name = '{}/{}.png'.format(output_dir, scenario.name.replace(' ', '_'))
            world.browser.driver.save_screenshot(image_name)
        except WebDriverException:
            LOGGER.error('Could not capture a screenshot')


@after.each_scenario
def capture_console_log(scenario):
    """
    Save the console log to help with debugging.
    """
    if scenario.failed:
        log = world.browser.driver.get_log('browser')
        try:
            output_dir = '{}/log'.format(settings.TEST_ROOT)
            file_name = '{}/{}.log'.format(output_dir, scenario.name.replace(' ', '_'))

            with open(file_name, 'w') as output_file:
                for line in log:
                    output_file.write("{}{}".format(dumps(line), '\n'))

        except WebDriverException:
            LOGGER.error('Could not capture the console log')


def capture_screenshot_for_step(step, when):
    """
    Useful method for debugging acceptance tests that are run in Vagrant.
    This method runs automatically before and after each step of an acceptance
    test scenario. The variable:

         world.auto_capture_screenshots

    either enables or disabled the taking of screenshots. To change the
    variable there is a convenient step defined:

        I (enable|disable) auto screenshots

    If you just want to capture a single screenshot at a desired point in code,
    you should use the method:

        world.capture_screenshot("image_name")
    """
    if world.auto_capture_screenshots:
        scenario_num = step.scenario.feature.scenarios.index(step.scenario) + 1
        step_num = step.scenario.steps.index(step) + 1
        step_func_name = step.defined_at.function.func_name
        image_name = "{prefix:03d}__{num:03d}__{name}__{postfix}".format(
            prefix=scenario_num,
            num=step_num,
            name=step_func_name,
            postfix=when
        )
        world.capture_screenshot(image_name)


@before.each_step
def before_each_step(step):
    capture_screenshot_for_step(step, '1_before')


@after.each_step
def after_each_step(step):
    capture_screenshot_for_step(step, '2_after')


@after.harvest
def teardown_browser(total):
    """
    Quit the browser after executing the tests.
    """
    if world.LETTUCE_SELENIUM_CLIENT == 'saucelabs':
        set_saucelabs_job_status(world.jobid, total.scenarios_ran == total.scenarios_passed)
    world.browser.quit()

"""
This config file extends the test environment configuration
so that we can run the lettuce acceptance tests on SauceLabs.
"""

# We intentionally define lots of variables that aren't used, and
# want to import all variables from base settings files
# pylint: disable=W0401, W0614

from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import os
import json

PORTS = [2000, 2001, 2020, 2109, 2222, 2310, 3000, 3001,
        3030, 3210, 3333, 4000, 4001, 4040, 4321, 4502, 4503, 5000, 5001,
        5050, 5555, 5432, 6000, 6001, 6060, 6666, 6543, 7000, 7070, 7774,
        7777, 8003, 8031, 8080, 8081, 8765, 8888, 9000, 9001,
        9080, 9090, 9876, 9999, 49221, 55001]

DESIRED_CAPABILITIES = {
    'chrome': DesiredCapabilities.CHROME,
    'internet explorer': DesiredCapabilities.INTERNETEXPLORER,
    'firefox': DesiredCapabilities.FIREFOX,
    'opera': DesiredCapabilities.OPERA,
    'iphone': DesiredCapabilities.IPHONE,
    'ipad': DesiredCapabilities.IPAD,
    'safari': DesiredCapabilities.SAFARI,
    'android': DesiredCapabilities.ANDROID
}

DEFAULT_CONFIG='{"PLATFORM":"Linux", "BROWSER":"chrome", "VERISON":"", "DEVICE":""}'

SAUCE_INFO = json.loads(os.environ.get('SAUCE_INFO', DEFAULT_CONFIG))

# Information needed to utilize Sauce Labs.
SAUCE = {
    'SAUCE_ENABLED': os.environ.get('SAUCE_ENABLED'),
    'USERNAME': os.environ.get('SAUCE_USER_NAME'),
    'ACCESS_ID': os.environ.get('SAUCE_API_KEY'),
    'BROWSER': DESIRED_CAPABILITIES.get(SAUCE_INFO.get('BROWSER', 'chrome').lower(), DesiredCapabilities.CHROME),
    'PLATFORM': SAUCE_INFO.get('PLATFORM', 'Linux'),
    'VERSION': SAUCE_INFO.get('VERSION', ''),
    'DEVICE': SAUCE_INFO.get('DEVICE', ''),
    'SESSION': 'Jenkins Acceptance Tests',
    'BUILD': os.environ.get('JOB_NAME', 'LETTUCE TESTS'),
}

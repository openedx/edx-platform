"""
This config file extends the test environment configuration
so that we can run the lettuce acceptance tests on SauceLabs.
"""

# We intentionally define lots of variables that aren't used, and
# want to import all variables from base settings files
# pylint: disable=wildcard-import, unused-wildcard-import

from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import os

PORTS = [
    2000, 2001, 2020, 2109, 2222, 2310, 3000, 3001,
    3030, 3210, 3333, 4000, 4001, 4040, 4321, 4502, 4503,
    5050, 5555, 5432, 6060, 6666, 6543, 7000, 7070, 7774,
    7777, 8003, 8031, 8080, 8081, 8765, 8888,
    9080, 9090, 9876, 9999, 49221, 55001
]

DESIRED_CAPABILITIES = {
    'chrome': DesiredCapabilities.CHROME,
    'internetexplorer': DesiredCapabilities.INTERNETEXPLORER,
    'firefox': DesiredCapabilities.FIREFOX,
    'opera': DesiredCapabilities.OPERA,
    'iphone': DesiredCapabilities.IPHONE,
    'ipad': DesiredCapabilities.IPAD,
    'safari': DesiredCapabilities.SAFARI,
    'android': DesiredCapabilities.ANDROID
}

# All keys must be URL and JSON encodable
# PLATFORM-BROWSER-VERSION_NUM-DEVICE
ALL_CONFIG = {
    'Linux-chrome--': ['Linux', 'chrome', '', ''],
    'Windows 8-chrome--': ['Windows 8', 'chrome', '', ''],
    'Windows 7-chrome--': ['Windows 7', 'chrome', '', ''],
    'Windows XP-chrome--': ['Windows XP', 'chrome', '', ''],
    'OS X 10.8-chrome--': ['OS X 10.8', 'chrome', '', ''],
    'OS X 10.6-chrome--': ['OS X 10.6', 'chrome', '', ''],

    'Linux-firefox-23-': ['Linux', 'firefox', '23', ''],
    'Windows 8-firefox-23-': ['Windows 8', 'firefox', '23', ''],
    'Windows 7-firefox-23-': ['Windows 7', 'firefox', '23', ''],
    'Windows XP-firefox-23-': ['Windows XP', 'firefox', '23', ''],

    'OS X 10.8-safari-6-': ['OS X 10.8', 'safari', '6', ''],

    'Windows 8-internetexplorer-10-': ['Windows 8', 'internetexplorer', '10', ''],
}

SAUCE_INFO = ALL_CONFIG.get(os.environ.get('SAUCE_INFO', 'Linux-chrome--'))

# Information needed to utilize Sauce Labs.
SAUCE = {
    'USERNAME': os.environ.get('SAUCE_USER_NAME'),
    'ACCESS_ID': os.environ.get('SAUCE_API_KEY'),
    'PLATFORM': SAUCE_INFO[0],
    'BROWSER': DESIRED_CAPABILITIES.get(SAUCE_INFO[1]),
    'VERSION': SAUCE_INFO[2],
    'DEVICE': SAUCE_INFO[3],
    'SESSION': 'Jenkins Acceptance Tests',
    'BUILD': os.environ.get('BUILD_DISPLAY_NAME', 'LETTUCE TESTS'),
}

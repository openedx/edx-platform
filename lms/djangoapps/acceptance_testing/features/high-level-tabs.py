from lettuce import * #before, world
from selenium import *
import lettuce_webdriver.webdriver
import logging
import nose.tools
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
import re

import os.path
import sys
path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static'))
if not path in sys.path:
    sys.path.insert(1, path)
del path
from helpers import *

@step(u'I access a registered course')
def i_access_a_registered_course(step):
	wait_until_class_renders('my-courses',1)
	world.browser.find_element_by_xpath("//*[@class='my-course']//a").click()
	wait_until_class_renders('content-wrapper',2)

@step(u'I click on "(.*)"')
def i_click_on_tab(step, tabname):
	world.browser.find_element_by_link_text(tabname).click()
	check_for_errors()
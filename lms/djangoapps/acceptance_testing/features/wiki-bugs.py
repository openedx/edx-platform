from lettuce import * #before, world
from selenium import *
import lettuce_webdriver.webdriver
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

@step(u'And I click on a child')
def and_i_click_on_a_child(step):
	world.browser.find_element_by_xpath("//table//tbody//tr[2]//td//a").click()

@step(u'Then I should not get a server error')
def then_i_should_not_get_a_server_error(step):
	wait_until_class_renders('global slim',2)
	check_for_errors()


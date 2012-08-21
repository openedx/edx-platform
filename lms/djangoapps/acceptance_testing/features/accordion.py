from lettuce import * #before, world
from selenium import *
import lettuce_webdriver.webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from helpers import *
import re
from courses import *


@step(u'I should see an element with class of "(.*)" within "(.*)" seconds')
def i_should_see_an_element_with_class_of_classname_within_duraion_seconds(step,classname,duration):
	wait_until_class_renders(classname, int(duration))

@step(u'I should see an element with class of "(.*)"')
def i_should_see_an_element_with_class_of_classname(step,classname):
	world.browser.find_element_by_class_name(classname)

@step(u'I click on every item in every week of the course')
def i_click_on_every_item_in_every_week_of_the_course(step):
	get_courseware()
	weeks = world.browser.find_elements_by_xpath("//*[@id='accordion']//nav//h3")
	for week in weeks:
		week.click()
		wait_until_class_renders('p',1)
		nodes = world.browser.find_elements_by_xpath("//*[@id='accordion']//nav//ul[@class='ui-accordion-content ui-helper-reset ui-widget-content ui-corner-bottom ui-accordion-content-active']//li")
		i = len(nodes)
		j = 1
		while j <= i:
			node = world.browser.find_element_by_xpath("//*[@id='accordion']//nav//ul[@class='ui-accordion-content ui-helper-reset ui-widget-content ui-corner-bottom ui-accordion-content-active']//li["+str(1)+"]//a//p")
			goodnodetext = re.sub(r'\s','_',node.text)
			node.click()
			j += 1
			clean = re.sub('\"','',goodnodetext)
			wait_until_id_renders("sequence_i4x-MITx-6_00x-sequential-"+clean,3)
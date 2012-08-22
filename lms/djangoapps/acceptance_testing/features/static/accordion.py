from lettuce import * #before, world
from selenium import *
import lettuce_webdriver.webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from helpers import *
import re


@step(u'I should see an element with class of "(.*)" within "(.*)" seconds')
def i_should_see_an_element_with_class_of_classname_within_duraion_seconds(step,classname,duration):
	wait_until_class_renders(classname, int(duration))

@step(u'I should see an element with class of "(.*)"')
def i_should_see_an_element_with_class_of_classname(step,classname):
	world.browser.find_element_by_class_name(classname)

@step(u'I click on every item in every week of the course')
def i_click_on_every_item_in_every_week_of_the_course(step):
	wait_until_id_renders('accordion',2)
	chapters = world.browser.find_elements_by_xpath("//*[@id='accordion']//nav//h3")
	num_chapters = len(chapters)
	k = 1
	while k <= num_chapters:

		world.browser.find_element_by_xpath("//*[@id='accordion']//nav//h3["+str(k)+"]").click()
		wait_until_class_renders('p',1)
		k+=1
		sections = world.browser.find_elements_by_xpath("//*[@id='accordion']//nav//ul[@class='ui-accordion-content ui-helper-reset ui-widget-content ui-corner-bottom ui-accordion-content-active']//li")
		i = len(sections)
		j = 1
		while j <= i:
			section = world.browser.find_element_by_xpath("//*[@id='accordion']//nav//ul[@class='ui-accordion-content ui-helper-reset ui-widget-content ui-corner-bottom ui-accordion-content-active']//li["+str(j)+"]//a//p")
			good_section_text = re.sub(r'\s','_',section.text)
			section.click()
			j += 1
			clean = re.sub('\"','',good_section_text)
			wait_until_id_renders("sequence_i4x-MITx-6_00x-sequential-"+clean,3)
			tabs = world.browser.find_elements_by_xpath("//ol[@id='sequence-list']//li")
			num_tabs = len(tabs)
			l = 1
			while l <= num_tabs:
				tab = world.browser.find_element_by_xpath("//ol[@id='sequence-list']//li["+str(l)+"]")
				#tab.click()
				tab.find_element_by_xpath("//a[@data-element='"+str(l)+"']").click()
				l+=1

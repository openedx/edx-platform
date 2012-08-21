from lettuce import * #before, world
from selenium import *
import lettuce_webdriver.webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from helpers import *

## Signup Step

@step(u'I signup with "(.*)" in the "(.*)" field')
def i_signup_with_data_in_the_field_field(step, data, field):
	e = find_element_by_name_in_selection('signup-modal',field)
	e.send_keys(data)

@step(u'I fill the "(.*)" field with "(.*)"')
def i_fill_the_field_with_value(step, field, value):
  field = world.browser.find_element_by_name(field);
  field.send_keys(value);

@step(u'I select "(.*)" from "(.*)"')
def i_select_option_from_selection(step, option, selection):
	select = world.browser.find_element_by_name(selection)
	allOptions = select.find_elements_by_tag_name("option")
	for option in allOptions:
	    if (option.text == "None"):
	    	option.click()

@step(u'I click the checkbox "(.*)"')
def i_click_the_checkbox(step, checkbox):
	e = find_element_by_name_in_selection('signup-modal',checkbox)
	e.click()

@step(u'I login with "(.*)"')
def i_login_with_text(step,text):
	e = find_element_by_name_in_selection('signup-modal',text)
	e.click()

@step(u'Then I should see an element with class of "([^"]*)" within "(.*)" seconds')
def then_i_should_see_an_element_with_class_of_classname_within_duration_seconds(step, classname, duration):
	wait_until_class_renders(classname, int(duration))

## Logout Step

@step(u'Given I am logged in')
def given_i_am_logged_in(step):
	pass

@step(u'I click the (.*) dropdown')
def i_logout(step,arg):
	dropdown = world.browser.find_element_by_xpath("//nav//ol[2]//li[2]//a")
	dropdown.click()

@step(u'Then I should see an element with id of "(.*)" within "(.*)" seconds')
def then_i_should_see_an_element_with_id_of_elementid_within_duration_seconds(step, element_id, duration):
	wait_until_id_renders(element_id, int(duration))

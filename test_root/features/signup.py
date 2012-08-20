from lettuce import * #before, world
from selenium import *
import lettuce_webdriver.webdriver
from selenium.webdriver import ActionChains

@step(u'I signup with "(.*)" in the "(.*)" field')
def i_signup_with_data_in_the_field_field(step, data, field):
	#e = world.browser.find_element_by_css_selector("div.input-group").find_element_by_name("email")
	e = world.browser.find_element_by_xpath("//section[@id='signup-modal']").find_element_by_name(field)
	e.send_keys(data)

@step(u'I fill the "(.*)" field with "(.*)"')
def i_fill_the_field_with_value(step, name, value):
  field = world.browser.find_element_by_name(name);
  field.send_keys(value);

@step(u'I select "(.*)" from "(.*)"')
def i_select_option_from_selection(step, option, selection):
	select = world.browser.find_element_by_name(selection)
	allOptions = select.find_elements_by_tag_name("option")
	for option in allOptions:
	    if (option.name == option):
	    	option.click()

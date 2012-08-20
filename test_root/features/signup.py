from lettuce import * #before, world
from selenium import *
import lettuce_webdriver.webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import WebDriverWait

## Signup Step

@step(u'I signup with "(.*)" in the "(.*)" field')
def i_signup_with_data_in_the_field_field(step, data, field):
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

@step(u'I click the checkbox "(.*)"')
def i_click_the_checkbox(step, checkbox):
	c = world.browser.find_element_by_xpath("//section[@id='signup-modal']").find_element_by_name(checkbox)
	c.click()

@step(u'Then I should see an element with class of "([^"]*)" within "(.*)" seconds')
def then_i_should_see_an_element_with_class_of_classname_within_duration_seconds(step, classname, duration):
	try:
		element = WebDriverWait(world.browser, int(duration)).until(lambda driver : driver.find_element_by_class_name(classname))
	finally:
		pass



## Logout Step

@step(u'I logout')
def i_logout(step):
	l = world.browser.find_element_by_link_text("/logout")
	l.click()


## Login Step

@step(u'I login with "(.*)" in the "(.*)" field')
def i_login_with_data_in_the_fieldname_field(step,data,fieldname):
	e = world.browser.find_element_by_xpath("//section[@id='login-modal']").find_element_by_name(fieldname)
	e.send_keys(data)
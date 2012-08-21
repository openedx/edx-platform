from lettuce import * #before, world
from selenium import *
import lettuce_webdriver.webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from helpers import *

## Login

url = 'http://anant:agarwal@sandbox-test-001.m.edx.org/'
#url = 'http://anant:agarwal@stage-edx-001.m.edx.org/'

@step(u'I login with "(.*)" in the "(.*)" field')
def i_login_with_data_in_the_fieldname_field(step,data,field):
	e = find_element_by_name_in_selection('login-modal',field)
	e.send_keys(data)

## I register for a course, unregister, then register again
course_list = ['MITx/6.00x/2012_Fall']

@step(u'Given I have a list of courses')
def get_list_of_courses(step):
	return course_list
#do some back-end code stuff here

@step(u'I register for every course')
def i_register_for_every_course(step):
	for course in course_list:
		register_for_course(course)

@step(u'I notice I have been registered for every course')
def i_notice_i_have_been_registered_for_every_course(step):
	for course in course_list:
		check_if_registered(course)

@step(u'I unregister for every course')
def i_unregister_for_every_course(step):
	for course in course_list:
		unregister_for_course(course)

@step(u'I notice I have been unregistered')
def i_notice_i_have_been_unregistered(step):
	world.browser.get(url+'dashboard')
	assert has_courses() == False

@step(u'I register for one course')
def i_click_on_one_course(step):
	register_for_course(course_list[0])

@step(u'Then I should see that course in my dashboard')
def then_i_should_see_that_course_in_my_dashboard(step):
	check_if_registered(course_list[0])


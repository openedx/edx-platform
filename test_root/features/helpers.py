from lettuce import * #before, world
from selenium import *
import lettuce_webdriver.webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import WebDriverWait

url = 'http://anant:agarwal@sandbox-test-001.m.edx.org/'
#url = 'http://anant:agarwal@stage-edx-001.m.edx.org/'

## Helper methods for selenium tests for EdX

#### Utility Methods

## Utility method for finding elements in a selection

def find_element_by_name_in_selection(selection_id, field):
	e = world.browser.find_element_by_xpath("//*[@id='"+selection_id+"']").find_element_by_name(field)
	return e

## Utility methods for waiting for elements to render

def wait_until_class_renders(class_name,time):
	try:
		e = WebDriverWait(world.browser, time).until(lambda driver : driver.find_element_by_class_name(class_name))
		return e
	except:
		return False

def wait_until_id_renders(element_id,time):
	try:
		e = WebDriverWait(world.browser, time).until(lambda driver : driver.find_element_by_id(element_id))
		return e
	except:
		return False

## Utility methods for courses

def has_courses():
	if wait_until_class_renders('empty-dashboard-message',3):
		return False
	else:
		return True

def register_for_course(coursename):
	world.browser.get(url+'courses')
	world.browser.find_element_by_xpath("//*[@id='"+coursename+"']//a[1]").click()
	wait_until_class_renders('register',3).click()

def check_if_registered(coursename):
	world.browser.get(url+'dashboard')
	world.browser.find_element_by_xpath("//a[@href='/courses/"+coursename+"/info']")

def unregister_for_course(coursename):
	world.browser.get(url+'dashboard')
	world.browser.find_element_by_xpath("//a[@data-course-id='"+coursename+"']").click()
	find_element_by_name_in_selection('unenroll_form','submit').click()

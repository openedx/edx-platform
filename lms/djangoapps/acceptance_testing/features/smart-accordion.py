from lettuce import * #before, world
from selenium import *
import lettuce_webdriver.webdriver
import logging
import nose.tools
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
import re

## imported from lms/djangoapps/courseware/courses.py
from collections import defaultdict
from fs.errors import ResourceNotFoundError
from functools import wraps
import logging

from path import path
from django.conf import settings
from django.http import Http404

from xmodule.course_module import CourseDescriptor
from xmodule.modulestore import Location
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError
from static_replace import replace_urls, try_staticfiles_lookup
from courseware.access import has_access
## end import

from django.core.urlresolvers import reverse
from courseware.courses import course_image_url, get_course_about_section, get_course_by_id
from courses import *
import os.path
import sys
path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static'))
if not path in sys.path:
    sys.path.insert(1, path)
del path
from helpers import *
	

@step(u'I verify all the content of each course')
def i_verify_all_the_content_of_each_course(step):
	all_possible_courses = get_courses()
	ids = [c.id for c in all_possible_courses]
	registered_courses = len(world.browser.find_elements_by_class_name("my-course"))
	if len(all_possible_courses) < registered_courses:
		assert False, "user is registered for more courses than are uniquely posssible"
	else:
		pass
	i = 0
	while i < registered_courses:
		world.browser.find_element_by_xpath("//section[@class='my-courses']//article["+str(i+1)+"]//a").click()
		wait_until_class_renders('my-courses',1)
		current_course = re.sub('/info','',re.sub('.*/courses/','',world.browser.current_url))
		validate_course(current_course,ids)
		

		#
		#validate_course_content(current_course)
		#



		world.browser.find_element_by_xpath("//a[@class='user-link']").click()
		i += 1



#	courses = get_courses()
#	for course in courses:
#		browse_course(course)


		## click on a course i'm registered for
		## extract the course id from the url
		## match it to the course id from get_courses() and then walkthrough

def browse_course(course_id):
	course = get_course_by_id(course_id)
	
		chapters = course.get_children()
		world.browser.get(base_url+'/courses/'+course+'/courseware')
		wait_until_id_renders('accordion',2)
		rendered_chapters = len(world.browser.find_elements_by_xpath("//*[@id='accordion']//nav//h3"))
		assert rendered_chapters == len(chapters)
		i = 0
		while i < len(chapters):
			world.browser.find_element_by_xpath("//*[@id='accordion']//nav//h3["+str(i+1)+"]").click()
			sections = chapter.get_children()
			accordion_class = "ui-accordion-content ui-helper-reset ui-widget-content ui-corner-bottom ui-accordion-content-active"
			rendered_sections = world.browser.find_element_by_xpath("//*[@id='accordion']//nav//ul[@class='"+accordion_class+"']//li")
			assert rendered_sections == len(sections)
			i += 1
			if world.browser.find_element_by_xpath("//section[@class='outside-app']"):
				assert False
			else:
				j = 0
				while j < len(sections):
					section = sections[j]

				#	course.id -> course url betwen /courses/(.*)/info
					j += 1


def validate_course(current_course, ids):
	try:
		ids.index(current_course)
	except:	
		assert False, "invalid course id"

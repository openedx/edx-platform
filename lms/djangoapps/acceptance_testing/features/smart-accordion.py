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
		check_for_errors()
		current_course = re.sub('/info','',re.sub('.*/courses/','',world.browser.current_url))
		
		validate_course(current_course,ids)
		
		world.browser.find_element_by_link_text('Courseware').click()
		wait_until_id_renders('accordion',2)
		check_for_errors()
		browse_course(current_course)

		world.browser.find_element_by_xpath("//a[@class='user-link']").click()
		check_for_errors()
		i += 1


def browse_course(course_id):
	world.browser.find_element_by_xpath("//div[@id='accordion']//nav//div[1]").click()

	wait_until_id_renders('accordion',2)
	check_for_errors()

	chapters = get_courseware_with_tabs(course_id)
	num_chapters = len(chapters)
	rendered_chapters = len(world.browser.find_elements_by_class_name("chapter"))
	
	assert num_chapters == rendered_chapters, '%d chapters expected, %d chapters found on page' % (num_chapters, rendered_chapters)
	
	chapter_it = 0

	## Iterate the chapters
	while chapter_it < num_chapters:
		world.browser.find_element_by_xpath("//*[@id='accordion']//nav//div["+str(chapter_it+1)+"]//h3").click()
		check_for_errors()

		sections = chapters[chapter_it]['sections']
		num_sections = len(sections)
		accordion_class = "ui-accordion-content ui-helper-reset ui-widget-content ui-corner-bottom ui-accordion-content-active"
		rendered_sections = len(world.browser.find_elements_by_xpath("//*[@id='accordion']//nav//div["+str(chapter_it+1)+"]//ul//li"))
		
		assert num_sections == rendered_sections, '%d sections expected, %d sections found on page, iteration number %d' % (num_sections, rendered_sections, chapter_it)
		
		section_it = 0
		## Iterate the sections
		while section_it < num_sections:
			world.browser.find_element_by_xpath("//*[@id='accordion']//nav//div["+str(chapter_it+1)+"]//ul[@class='"+accordion_class+"']//li["+str(section_it+1)+"]//a").click()
			wait_until_class_renders('course-content',3)
			check_for_errors()

			#tab = current_course.get_children()[0].get_children()[0]
			num_tabs = sections[section_it]['clickable_tab_count']
			if num_tabs != 0:
				rendered_tabs = len(world.browser.find_elements_by_xpath("//ol[@id='sequence-list']//li"))
			else:
				rendered_tabs = 0

			assert num_tabs == rendered_tabs ,'%d tabs expected, %d tabs found, iteration number %d' % (num_tabs,rendered_tabs,section_it)
			
			## Iterate the tabs
			tab_it = 0
			while tab_it < num_tabs:
				tab = world.browser.find_element_by_xpath("//ol[@id='sequence-list']//li["+str(tab_it+1)+"]//a[@data-element='"+str(tab_it+1)+"']")
				tab.click()
				check_for_errors()
				
				tab_it += 1

			section_it += 1
		
		chapter_it += 1



def validate_course(current_course, ids):
	try:
		ids.index(current_course)
	except:	
		assert False, "invalid course id"

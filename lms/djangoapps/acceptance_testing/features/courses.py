from lettuce import * #before, world
from selenium import *
import lettuce_webdriver.webdriver
import logging
import nose.tools
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import WebDriverWait

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
from courseware.courses import course_image_url, get_course_about_section

## support functions
def get_courses():
  '''
  Returns dict of lists of courses available, keyed by course.org (ie university).
  Courses are sorted by course.number.
  '''
  courses = [c for c in modulestore().get_courses()
             if isinstance(c, CourseDescriptor)]
  courses = sorted(courses, key=lambda course: course.number)
  logging.info("COURSES FOUND")
  logging.info(courses)

  return courses

## course listing step
@step(u'I should see all courses')
def i_should_see_all_courses(step):
  courses = get_courses()
  page_source = world.browser.page_source

  course_link_texts = [ (c.location.course, c.display_name) for c in courses]
  for c in course_link_texts:
    assert world.browser.find_element_by_partial_link_text(c[0] + ' ' + c[1])

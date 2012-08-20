from lettuce import * #before, world
from selenium import *
import lettuce_webdriver.webdriver
import logging
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import WebDriverWait

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

## set up logger
# logging.basicConfig(filename='lettuce.log', level=logging.DEBUG)

## support functions
def get_courses():
  '''
  Returns dict of lists of courses available, keyed by course.org (ie university).
  Courses are sorted by course.number.
  '''
  # TODO: Clean up how 'error' is done.
  # filter out any courses that errored.
  courses = [c for c in modulestore().get_courses()
             if isinstance(c, CourseDescriptor)]
  courses = sorted(courses, key=lambda course: course.number)

  logging.debug(courses)

## course listing step
@step(u'I should see all courses')
def i_should_see_all_courses(step):
  get_courses()
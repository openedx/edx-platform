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
from courseware.courses import course_image_url, get_course_about_section, get_course_by_id

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

def get_courseware(course_id):
  """
  Given a course_id (string), return a courseware array of dictionaries for the
  top two levels of navigation. Example:

  [
    {'chapter_name': 'Overview', 
     'sections': ['Welcome', 'System Usage Sequence', 'Lab0: Using the tools', 'Circuit Sandbox']
    },
    {'chapter_name': 'Week 1',
     'sections': ['Administrivia and Circuit Elements', 'Basic Circuit Analysis', 'Resistor Divider', 'Week 1 Tutorials']
     },
    {'chapter_name': 'Midterm Exam',
     'sections': ['Midterm Exam']
    }
  ]
  """

  course = get_course_by_id(course_id)
  chapters = course.get_children()
  courseware = [ {'chapter_name':c.display_name, 'sections':[s.display_name for s in c.get_children()]} for c in chapters]
  return courseware

## course listing step
@step(u'I should see all courses')
def i_should_see_all_courses(step):
  courses = get_courses()
  
  course_link_texts = [ (c.location.course, c.display_name) for c in courses]
  for c in course_link_texts:
    assert world.browser.find_element_by_partial_link_text(c[0] + ' ' + c[1])



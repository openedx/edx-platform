from lettuce import world, step
import re
from nose.tools import assert_equals

## imported from lms/djangoapps/courseware/courses.py
from collections import defaultdict
from fs.errors import ResourceNotFoundError
from functools import wraps

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
#from helpers import *

from logging import getLogger
logger = getLogger(__name__)

def check_for_errors():
    e = world.browser.find_by_css('.outside-app')
    if len(e) > 0:
        assert False, 'there was a server error at %s' % (world.browser.url)
    else:
        assert True

@step(u'I verify all the content of each course')
def i_verify_all_the_content_of_each_course(step):
    all_possible_courses = get_courses()
    ids = [c.id for c in all_possible_courses]

    # Get a list of all the registered courses
    registered_courses = world.browser.find_by_css('article.my-course')
    if len(all_possible_courses) < len(registered_courses):
        assert False, "user is registered for more courses than are uniquely posssible"
    else:
        pass

    for test_course in registered_courses:
        test_course.find_by_css('a').click()
        check_for_errors()

        # Get the course. E.g. 'MITx/6.002x/2012_Fall'
        current_course = re.sub('/info','',re.sub('.*/courses/','',world.browser.url))
        validate_course(current_course,ids)

        world.browser.find_link_by_text('Courseware').click()
        assert world.browser.is_element_present_by_id('accordion',wait_time=2)
        check_for_errors()
        browse_course(current_course)

        # clicking the user link gets you back to the user's home page
        world.browser.find_by_css('.user-link').click()
        check_for_errors()

def browse_course(course_id):

    ## count chapters from xml and page and compare
    chapters = get_courseware_with_tabs(course_id)
    num_chapters = len(chapters)
    rendered_chapters = world.browser.find_by_css('#accordion > nav > div')
    num_rendered_chapters = len(rendered_chapters)
    assert num_chapters == num_rendered_chapters, '%d chapters expected, %d chapters found on page for %s' % (num_chapters, num_rendered_chapters, course_id)

    chapter_it = 0

    ## Iterate the chapters
    while chapter_it < num_chapters:

        ## click into a chapter
        world.browser.find_by_css('#accordion > nav > div')[chapter_it].find_by_tag('h3').click()

        ## look for the "there was a server error" div
        check_for_errors()

        ## count sections from xml and page and compare
        sections = chapters[chapter_it]['sections']
        num_sections = len(sections)

        rendered_sections = world.browser.find_by_css('#accordion > nav > div')[chapter_it].find_by_tag('li')
        num_rendered_sections = len(rendered_sections)
        assert num_sections == num_rendered_sections, '%d sections expected, %d sections found on page, iteration number %d on %s' % (num_sections, num_rendered_sections, chapter_it, course_id)

        section_it = 0

        ## Iterate the sections
        while section_it < num_sections:

            ## click on a section
            world.browser.find_by_css('#accordion > nav > div')[chapter_it].find_by_tag('li')[section_it].find_by_tag('a').click()

            ## sometimes the course-content takes a long time to load
            assert world.browser.is_element_present_by_css('.course-content',wait_time=5)

            ## look for server error div
            check_for_errors()

            ## count tabs from xml and page and compare

            ## count the number of tabs. If number of tabs is 0, there won't be anything rendered
            ## so we explicitly set rendered_tabs because otherwise find_elements returns a None object with no length
            num_tabs = sections[section_it]['clickable_tab_count']
            if num_tabs != 0:
                rendered_tabs = world.browser.find_by_css('ol#sequence-list > li')
                num_rendered_tabs = len(rendered_tabs)
            else:
                rendered_tabs = 0
                num_rendered_tabs = 0

            assert num_tabs == num_rendered_tabs ,'%d tabs expected, %d tabs found, iteration number %d, on %s' % (num_tabs,num_rendered_tabs,section_it, course_id)

            tab_it = 0

            ## Iterate the tabs
            while tab_it < num_tabs:

                rendered_tabs[tab_it].find_by_tag('a').click()

                ## do something with the tab sections[section_it]
                check_for_errors()

                tab_it += 1

            section_it += 1

        chapter_it += 1


def validate_course(current_course, ids):
    try:
        ids.index(current_course)
    except:
        assert False, "invalid course id"

from lettuce import * #before, world
from selenium import *
#import lettuce_webdriver.webdriver
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
#from helpers import *


@step(u'I visit and check 502 for "(.*)"')
def i_visit_and_check_502_for_url(step, url):
    world.browser.get(url)
    check_for_502(url)

@step(u'I process')
def i_make_sure_everything_is_there(step):
    e = world.browser.find_element_by_css_selector('section.course-content section')
    process_section(e)


def process_section(element, num_tabs=0):
    '''
    Process section reads through whatever is in 'course-content' and classifies it according to sequence module type.

    This function is recursive

    There are 5 types, with 5 actions.

    Sequence Module
    -contains one child module
    -to prevent from over-processing all its children (no easy way to specify only one level of depth), we only grab the first child

    Vertical Module
    -contains other modules
    -process it and get its children, then process them

    Capa Module
    -problem type, contains only one problem
    -for this, the most complex type, we created a separate method, process_problem

    Video Module
    -video type, contains only one video
    -we only check to ensure that a section with class of video exists

    Custom Tag Module
    -a custom 'hack' module type
    -there is a large variety of content that could go in a custom tag module, so we just pass if it is of this unusual type
    '''
    tab_type = element.get_attribute('class')
    print 'processing a %s' % (tab_type)
    if tab_type == "xmodule_display xmodule_SequenceModule":
        child_modules = element.find_elements_by_css_selector("section[class^='xmodule']")

        ## ugly bit of code to get around not being able to specify only the first level of descendants
        if child_modules[0].get_attribute('class') == "xmodule_display xmodule_VerticalModule":
            process_section(child_modules[0])
        else:
            for mod in child_modules:
                process_section(mod)

    elif tab_type == "xmodule_display xmodule_VerticalModule":
        vert_list = element.find_elements_by_css_selector("li section[class^='xmodule']")
        print "I found %s items" % (str(len(vert_list)))
        for item in vert_list:
            print 'processing a child %s' % (item.get_attribute('class'))
            process_section(item)

    elif tab_type == "xmodule_display xmodule_CapaModule":
        assert element.find_element_by_css_selector("section[id^='problem']") , "No problems found in %s" % (tab_type)
        p = element.find_element_by_css_selector("section[id^='problem']")
        p_id = p.get_attribute('id')
        process_problem(p, p_id)

    elif tab_type == "xmodule_display xmodule_VideoModule":
        assert element.find_element_by_css_selector("section[class^='video']") , 'No video found in %s' % (tab_type)

    elif tab_type == "xmodule_display xmodule_CustomTagModule":
        pass

    else:
        assert False, "%s not recognized!!" % (tab_type)



def process_problem(element, problem_id):
    '''
    Process problem attempts to
    1) scan all the input fields and reset them
    2) click the 'check' button and look for an incorrect response (p.status text should be 'incorrect')
    3) click the 'show answer' button IF it exists and IF the answer is not already displayed
    4) enter the correct answer in each input box
    5) click the 'check' button and verify that answers are correct

    Because of all the ajax calls happening, sometimes the test fails because objects disconnect from the DOM.
    The basic functionality does exist, though, and I'm hoping that someone can take it over and make it super effective.
    '''

    prob_xmod = element.find_element_by_css_selector("section.problem")
    input_fields = prob_xmod.find_elements_by_css_selector("section[id^='textinput']")

    ## clear out all input to ensure an incorrect result
    for field in input_fields:
        box = field.find_element_by_css_selector("input")
        box.clear()
        print "\n I cleared out the box %s \n" % (box.get_attribute('id'))

    ## because of cookies or the application, only click the 'check' button if the status is not already 'incorrect'
    if prob_xmod.find_element_by_css_selector("p.status").text.lower() != 'incorrect':
        prob_xmod.find_element_by_css_selector("section.action input.check").click()
        world.browser.implicitly_wait(4)

    ## all elements become disconnected after the click
    element = world.browser.find_element_by_css_selector("section[id='"+problem_id+"']")
    prob_xmod = element.find_element_by_css_selector("section.problem")
    input_fields = prob_xmod.find_elements_by_css_selector("section[id^='textinput']")
    for field in input_fields:
        assert field.find_element_by_css_selector("div.incorrect") , "The 'check' button did not work for %s" % (problem_id)
        print "\n So far so good! \n"


    ## wait for the ajax changes to render
    world.browser.implicitly_wait(4)

    ## grab element and prob_xmod because the dom has changed (some classes/elements became hidden and changed the hierarchy)
    element = world.browser.find_element_by_css_selector("section[id='"+problem_id+"']")
    prob_xmod = element.find_element_by_css_selector("section.problem")


    show_button = element.find_element_by_css_selector("section.action input.show")
    ## this logic is to ensure we do not accidentally hide the answers
    if show_button.get_attribute('value').lower() == 'show answer':
        show_button.click()
        print "\n I clicked show for %s \n" % (problem_id)
    else:
        pass


    ## wait for the ajax changes to render
    world.browser.implicitly_wait(4)

    ## grab element and prob_xmod because the dom has changed (some classes/elements became hidden and changed the hierarchy)
    element = world.browser.find_element_by_css_selector("section[id='"+problem_id+"']")
    prob_xmod = element.find_element_by_css_selector("section.problem")

    ## find all the input fields
    input_fields = prob_xmod.find_elements_by_css_selector("section[id^='textinput']")

    ## in each field, find the answer, and send it to the field.
    ## Note that this does not work if the answer type is a strange format, e.g. "either a or b"
    for field in input_fields:
        field.find_element_by_css_selector("input").send_keys(field.find_element_by_css_selector("p[id^='answer']").text)
        print "\n \n Entered %s into %s \n \n" % (field.find_element_by_css_selector("p[id^='answer']").text,field.find_element_by_css_selector("input").get_attribute('id') )
    prob_xmod = element.find_element_by_css_selector("section.problem")
    prob_xmod.find_element_by_css_selector("section.action input.check").click()
    world.browser.implicitly_wait(4)

    ## assert that we entered the correct answers
    ## we have to redefine input-fields because apparently they become detached from the dom after clicking 'check'

    input_fields = world.browser.find_elements_by_css_selector("section[id='"+problem_id+"'] section[id^='textinput']")
    for field in input_fields:
        ## if you don't use 'starts with ^=' the test will fail because the actual class is 'correct ' (with a space)
        assert world.browser.find_element_by_css_selector("div[class^='correct']"), "The check answer values were not correct for %s" % (problem_id)
    inputs = world.browser.find_elements_by_css_selector("section[id^='textinput'] input")
    for el in inputs:
        el.clear()
    print "\n checked answers for %s \n" % (problem_id)

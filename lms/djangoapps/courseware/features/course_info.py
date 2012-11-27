from lettuce import world, step
from lettuce.django import django_url
#from portal.common import *

@step('I am on an info page')
def i_am_on_an_info_page(step):
    title = world.browser.title
    url = world.browser.url
    assert ('Course Info' in title)
    assert (r'/info' in url)

@step('I visit the course info URL$')
def i_visit_the_course_info_url(step):
    url = django_url('/courses/MITx/6.002x/2012_Fall/info')
    world.browser.visit(url)

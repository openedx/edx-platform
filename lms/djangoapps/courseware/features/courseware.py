# pylint: disable=missing-docstring
# pylint: disable=redefined-outer-name

from lettuce import world, step
from lettuce.django import django_url


@step('I visit the courseware URL$')
def i_visit_the_course_info_url(step):
    url = django_url('/courses/MITx/6.002x/2012_Fall/courseware')
    world.browser.visit(url)

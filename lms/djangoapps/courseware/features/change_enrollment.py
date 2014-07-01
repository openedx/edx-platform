from __future__ import absolute_import

import time

from lettuce import world, step
from lettuce.django import django_url
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from student.models import CourseEnrollment
from xmodule.modulestore.django import modulestore
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from xmodule.course_module import CourseDescriptor
from courseware.courses import get_course_by_id
from xmodule import seq_module, vertical_module

from logging import getLogger
logger = getLogger(__name__)




@step(u'the course "([^"]*)" has all enrollment modes$')
def add_enrollment_modes_to_course(step,course):
    world.CourseModeFactory.create(
        course_id = SlashSeparatedCourseKey("edx",course,'Test_Course'),
        mode_slug="verified",
        mode_display_name="Verified Course",
        min_price=3
    )
    world.CourseModeFactory.create(
        course_id = SlashSeparatedCourseKey("edx",course,'Test_Course'),
        mode_slug="honor",
        mode_display_name="Honor Course",
    )

    world.CourseModeFactory.create(
        course_id = SlashSeparatedCourseKey("edx",course,'Test_Course'),
        mode_slug="audit",
        mode_display_name="Audit Course",
    )


@step(u'I click on Challenge Yourself$')
def challenge_yourself(step):
    challenge_button = world.browser.find_by_css('.wrapper-tip')
    challenge_button.click()
    verified_button = world.browser.find_by_css('#upgrade-to-verified')
    verified_button.click()

@step(u'I choose an honor code upgrade$')
def honor_code_upgrade(step):
    honor_code_link = world.browser.find_by_css('.title-expand')
    honor_code_link.click()
    honor_code_checkbox = world.browser.find_by_css('#honor-code')
    honor_code_checkbox.click()
    upgrade_button = world.browser.find_by_name("certificate_mode")
    upgrade_button.click()

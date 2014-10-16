""" Provides lettuce acceptance methods for course enrollment changes """

from __future__ import absolute_import
from lettuce import world, step
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from logging import getLogger
logger = getLogger(__name__)

import time


@step(u'the course "([^"]*)" has all enrollment modes$')
def add_enrollment_modes_to_course(_step, course):
    """ Add honor, audit, and verified modes to the sample course """
    world.CourseModeFactory.create(
        course_id=SlashSeparatedCourseKey("edx", course, 'Test_Course'),
        mode_slug="verified",
        mode_display_name="Verified Course",
        min_price=3
    )
    world.CourseModeFactory.create(
        course_id=SlashSeparatedCourseKey("edx", course, 'Test_Course'),
        mode_slug="honor",
        mode_display_name="Honor Course",
    )

    world.CourseModeFactory.create(
        course_id=SlashSeparatedCourseKey("edx", course, 'Test_Course'),
        mode_slug="audit",
        mode_display_name="Audit Course",
    )


@step(u'I click on Challenge Yourself$')
def challenge_yourself(_step):
    """ Simulates clicking 'Challenge Yourself' button on course """
    challenge_button = world.browser.find_by_css('.wrapper-tip')
    challenge_button.click()
    verified_button = world.browser.find_by_css('#upgrade-to-verified')
    verified_button.click()


@step(u'I choose an honor code upgrade$')
def honor_code_upgrade(_step):
    """ Simulates choosing the honor code mode on the upgrade page """
    honor_code_link = world.browser.find_by_css('.title-expand')
    honor_code_link.click()
    time.sleep(1)
    honor_code_checkbox = world.browser.find_by_css('#honor-code')
    honor_code_checkbox.click()
    upgrade_button = world.browser.find_by_name("certificate_mode")
    upgrade_button.click()

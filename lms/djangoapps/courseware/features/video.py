#pylint: disable=C0111

from lettuce import world, step
from lettuce.django import django_url
from common import TEST_COURSE_NAME, TEST_SECTION_NAME, i_am_registered_for_the_course, section_location

############### ACTIONS ####################


@step('when I view the video it has autoplay enabled')
def does_autoplay(_step):
    assert(world.css_find('.video')[0]['data-autoplay'] == 'True')


@step('the course has a Video component')
def view_video(_step):
    coursename = TEST_COURSE_NAME.replace(' ', '_')
    i_am_registered_for_the_course(step, coursename)

    # Make sure we have a video
    add_video_to_course(coursename)
    chapter_name = TEST_SECTION_NAME.replace(" ", "_")
    section_name = chapter_name
    url = django_url('/courses/edx/Test_Course/Test_Course/courseware/%s/%s' %
                     (chapter_name, section_name))

    world.browser.visit(url)


@step('the course has a VideoAlpha component')
def view_videoalpha(step):
    coursename = TEST_COURSE_NAME.replace(' ', '_')
    i_am_registered_for_the_course(step, coursename)

    # Make sure we have a videoalpha
    add_videoalpha_to_course(coursename)
    chapter_name = TEST_SECTION_NAME.replace(" ", "_")
    section_name = chapter_name
    url = django_url('/courses/edx/Test_Course/Test_Course/courseware/%s/%s' %
                     (chapter_name, section_name))

    world.browser.visit(url)


def add_video_to_course(course):
    world.ItemFactory.create(parent_location=section_location(course),
                             category='video',
                             display_name='Video')


def add_videoalpha_to_course(course):
    category = 'videoalpha'
    world.ItemFactory.create(parent_location=section_location(course),
                             category=category,
                             display_name='Video Alpha')

#pylint: disable=C0111

from lettuce import world, step
from common import *

############### ACTIONS ####################


@step('when I view it it does autoplay')
def does_autoplay(step):
    assert(world.css_find('.video')[0]['data-autoplay'] == 'True')


@step('the course has a Video component')
def view_video(step):
    coursename = TEST_COURSE_NAME.replace(' ', '_')
    i_am_registered_for_the_course(step, coursename)

    # Make sure we have a video
    video = add_video_to_course(coursename)
    chapter_name = TEST_SECTION_NAME.replace(" ", "_")
    section_name = chapter_name
    url = django_url('/courses/edx/Test_Course/Test_Course/courseware/%s/%s' %
                     (chapter_name, section_name))

    world.browser.visit(url)


def add_video_to_course(course):
    template_name = 'i4x://edx/templates/video/default'
    world.ItemFactory.create(parent_location=section_location(course),
                             template=template_name,
                             display_name='Video')

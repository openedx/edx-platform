#pylint: disable=C0111
#pylint: disable=W0621

from lettuce import world, step
from common import *

############### ACTIONS ####################


@step('when I view it it does autoplay')
def does_autoplay(step):
    assert world.css_find('.video')[0]['data-autoplay'] == 'True'
    assert world.css_find('.video_control')[0].has_class('pause')

@step('the course has a Video component')
def view_video(step):
    model_course = 'model_course'
    coursename = TEST_COURSE_NAME.replace(' ', '_')
    i_am_registered_for_the_course(step, coursename)
    # Make sure we have a video
    video = create_video_component(coursename)
    url = django_url('/courses/edx/%s/Test_Course/courseware/' % model_course)
    world.browser.visit(url)
    print('\n\n\n')
    print world.browser.html
    print('\n\n\n')


def create_video_component(course):
    return world.ItemFactory.create(parent_location=section_location(course),
                                    template='i4x://edx/templates/video/default')

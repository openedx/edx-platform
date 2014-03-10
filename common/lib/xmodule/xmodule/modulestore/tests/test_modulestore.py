from nose.tools import assert_equals, assert_raises  # pylint: disable=E0611

from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.modulestore.search import path_to_location
from xmodule.modulestore.keys import CourseKey


def check_path_to_location(modulestore):
    """
    Make sure that path_to_location works: should be passed a modulestore
    with the toy and simple courses loaded.
    """
    course_id = CourseKey.from_string("edX/toy/2012_Fall")

    should_work = (
        (course_id.make_usage_key('video', 'Welcome'),
         (course_id, "Overview", "Welcome", None)),
        (course_id.make_usage_key('chapter', 'Overview'),
         (course_id, "Overview", None, None)),
    )

    for location, expected in should_work:
        assert_equals(path_to_location(modulestore, location), expected)

    not_found = (
        course_id.make_usage_key('video', 'WelcomeX'),
        course_id.make_usage_key('course', 'NotHome'),
    )
    for location in not_found:
        with assert_raises(ItemNotFoundError):
            path_to_location(modulestore, location)

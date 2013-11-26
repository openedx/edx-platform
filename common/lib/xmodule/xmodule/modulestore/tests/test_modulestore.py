from nose.tools import assert_equals, assert_raises  # pylint: disable=E0611

from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.modulestore.search import path_to_location

def check_path_to_location(modulestore):
    """
    Make sure that path_to_location works: should be passed a modulestore
    with the toy and simple courses loaded.
    """
    should_work = (
        ("i4x://edX/toy/video/Welcome",
         ("edX/toy/2012_Fall", "Overview", "Welcome", None)),
        ("i4x://edX/toy/chapter/Overview",
         ("edX/toy/2012_Fall", "Overview", None, None)),
    )
    course_id = "edX/toy/2012_Fall"

    for location, expected in should_work:
        assert_equals(path_to_location(modulestore, course_id, location), expected)

    not_found = (
        "i4x://edX/toy/video/WelcomeX", "i4x://edX/toy/course/NotHome"
    )
    for location in not_found:
        assert_raises(ItemNotFoundError, path_to_location, modulestore, course_id, location)

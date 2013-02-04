from nose.tools import assert_equals
from static_replace import replace_static_urls, replace_course_urls

DATA_DIRECTORY = 'data_dir'
COURSE_ID = 'org/course/run'


def test_multi_replace():
    static_source = '"/static/file.png"'
    course_source = '"/course/file.png"'

    assert_equals(
        replace_static_urls(static_source, DATA_DIRECTORY),
        replace_static_urls(replace_static_urls(static_source, DATA_DIRECTORY), DATA_DIRECTORY)
    )
    assert_equals(
        replace_course_urls(course_source, COURSE_ID),
        replace_course_urls(replace_course_urls(course_source, COURSE_ID), COURSE_ID)
    )
    assert False

from nose.tools import assert_equals
from static_replace import replace_static_urls, replace_course_urls
from mock import patch, Mock
from xmodule.modulestore import Location
from xmodule.modulestore.mongo import MongoModuleStore

DATA_DIRECTORY = 'data_dir'
COURSE_ID = 'org/course/run'
NAMESPACE = Location('org', 'course', 'run', None, None)


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


@patch('static_replace.finders')
@patch('static_replace.settings')
def test_debug_no_modify(mock_settings, mock_finders):
    mock_settings.DEBUG = True
    mock_finders.find.return_value = True

    static_source = '"/static/file.png"'
    assert_equals(static_source, replace_static_urls(static_source, DATA_DIRECTORY))

    mock_finders.find.assert_called_once_with('file.png', True)


@patch('static_replace.StaticContent')
@patch('static_replace.modulestore')
def test_mongo_filestore(mock_modulestore, mock_static_content):

    mock_modulestore.return_value = Mock(MongoModuleStore)
    mock_static_content.convert_legacy_static_url.return_value = "c4x://mock_url"

    static_source = '"/static/file.png"'

    # No namespace => no change to path
    assert_equals(static_source, replace_static_urls(static_source, DATA_DIRECTORY))

    # Namespace => content url
    assert_equals(
        '"' + mock_static_content.convert_legacy_static_url.return_value + '"',
        replace_static_urls(static_source, DATA_DIRECTORY, NAMESPACE)
    )

    mock_static_content.convert_legacy_static_url.assert_called_once_with('file.png', NAMESPACE)

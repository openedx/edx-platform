import re

from nose.tools import assert_equals, assert_true, assert_false  # pylint: disable=no-name-in-module
from static_replace import (
    replace_static_urls,
    replace_course_urls,
    _url_replace_regex,
    process_static_urls,
    make_static_urls_absolute
)
from mock import patch, Mock

from opaque_keys.edx.locations import SlashSeparatedCourseKey
from xmodule.modulestore.mongo import MongoModuleStore
from xmodule.modulestore.xml import XMLModuleStore

DATA_DIRECTORY = 'data_dir'
COURSE_KEY = SlashSeparatedCourseKey('org', 'course', 'run')
STATIC_SOURCE = '"/static/file.png"'


def test_multi_replace():
    course_source = '"/course/file.png"'

    assert_equals(
        replace_static_urls(STATIC_SOURCE, DATA_DIRECTORY),
        replace_static_urls(replace_static_urls(STATIC_SOURCE, DATA_DIRECTORY), DATA_DIRECTORY)
    )
    assert_equals(
        replace_course_urls(course_source, COURSE_KEY),
        replace_course_urls(replace_course_urls(course_source, COURSE_KEY), COURSE_KEY)
    )


def test_process_url():
    def processor(__, prefix, quote, rest):  # pylint: disable=missing-docstring
        return quote + 'test' + prefix + rest + quote

    assert_equals('"test/static/file.png"', process_static_urls(STATIC_SOURCE, processor))


def test_process_url_data_dir_exists():
    base = '"/static/{data_dir}/file.png"'.format(data_dir=DATA_DIRECTORY)

    def processor(original, prefix, quote, rest):  # pylint: disable=unused-argument,missing-docstring
        return quote + 'test' + rest + quote

    assert_equals(base, process_static_urls(base, processor, data_dir=DATA_DIRECTORY))


def test_process_url_no_match():

    def processor(__, prefix, quote, rest):  # pylint: disable=missing-docstring
        return quote + 'test' + prefix + rest + quote

    assert_equals('"test/static/file.png"', process_static_urls(STATIC_SOURCE, processor))


@patch('django.http.HttpRequest')
def test_static_urls(mock_request):
    mock_request.build_absolute_uri = lambda url: 'http://' + url
    result = make_static_urls_absolute(mock_request, STATIC_SOURCE)
    assert_equals(result, '\"http:///static/file.png\"')


@patch('static_replace.staticfiles_storage')
def test_storage_url_exists(mock_storage):
    mock_storage.exists.return_value = True
    mock_storage.url.return_value = '/static/file.png'

    assert_equals('"/static/file.png"', replace_static_urls(STATIC_SOURCE, DATA_DIRECTORY))
    mock_storage.exists.called_once_with('file.png')
    mock_storage.url.called_once_with('data_dir/file.png')


@patch('static_replace.staticfiles_storage')
def test_storage_url_not_exists(mock_storage):
    mock_storage.exists.return_value = False
    mock_storage.url.return_value = '/static/data_dir/file.png'

    assert_equals('"/static/data_dir/file.png"', replace_static_urls(STATIC_SOURCE, DATA_DIRECTORY))
    mock_storage.exists.called_once_with('file.png')
    mock_storage.url.called_once_with('file.png')


@patch('static_replace.StaticContent')
@patch('static_replace.modulestore')
def test_mongo_filestore(mock_modulestore, mock_static_content):

    mock_modulestore.return_value = Mock(MongoModuleStore)
    mock_static_content.convert_legacy_static_url_with_course_id.return_value = "c4x://mock_url"

    # No namespace => no change to path
    assert_equals('"/static/data_dir/file.png"', replace_static_urls(STATIC_SOURCE, DATA_DIRECTORY))

    # Namespace => content url
    assert_equals(
        '"' + mock_static_content.convert_legacy_static_url_with_course_id.return_value + '"',
        replace_static_urls(STATIC_SOURCE, DATA_DIRECTORY, course_id=COURSE_KEY)
    )

    mock_static_content.convert_legacy_static_url_with_course_id.assert_called_once_with('file.png', COURSE_KEY)


@patch('static_replace.settings')
@patch('static_replace.modulestore')
@patch('static_replace.staticfiles_storage')
def test_data_dir_fallback(mock_storage, mock_modulestore, mock_settings):
    mock_modulestore.return_value = Mock(XMLModuleStore)
    mock_storage.url.side_effect = Exception

    mock_storage.exists.return_value = True
    assert_equals('"/static/data_dir/file.png"', replace_static_urls(STATIC_SOURCE, DATA_DIRECTORY))

    mock_storage.exists.return_value = False
    assert_equals('"/static/data_dir/file.png"', replace_static_urls(STATIC_SOURCE, DATA_DIRECTORY))


def test_raw_static_check():
    """
    Make sure replace_static_urls leaves alone things that end in '.raw'
    """
    path = '"/static/foo.png?raw"'
    assert_equals(path, replace_static_urls(path, DATA_DIRECTORY))

    text = 'text <tag a="/static/js/capa/protex/protex.nocache.js?raw"/><div class="'
    assert_equals(path, replace_static_urls(path, text))


@patch('static_replace.staticfiles_storage')
@patch('static_replace.modulestore')
def test_static_url_with_query(mock_modulestore, mock_storage):
    """
    Make sure that for urls with query params:
     query params that contain "^/static/" are converted to full location urls
     query params that do not contain "^/static/" are left unchanged
    """
    mock_storage.exists.return_value = False
    mock_modulestore.return_value = Mock(MongoModuleStore)

    pre_text = 'EMBED src ="/static/LAlec04_controller.swf?csConfigFile=/static/LAlec04_config.xml&name1=value1&name2=value2"'
    post_text = 'EMBED src ="/c4x/org/course/asset/LAlec04_controller.swf?csConfigFile=%2Fc4x%2Forg%2Fcourse%2Fasset%2FLAlec04_config.xml&name1=value1&name2=value2"'
    assert_equals(post_text, replace_static_urls(pre_text, DATA_DIRECTORY, COURSE_KEY))


def test_regex():
    yes = ('"/static/foo.png"',
           '"/static/foo.png"',
           "'/static/foo.png'")

    no = ('"/not-static/foo.png"',
          '"/static/foo',  # no matching quote
          )

    regex = _url_replace_regex('/static/')

    for s in yes:
        print 'Should match: {0!r}'.format(s)
        assert_true(re.match(regex, s))

    for s in no:
        print 'Should not match: {0!r}'.format(s)
        assert_false(re.match(regex, s))

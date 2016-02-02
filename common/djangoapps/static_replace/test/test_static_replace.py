"""Tests for static_replace"""

from urllib import quote_plus

import ddt
import re
from PIL import Image
from cStringIO import StringIO

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
from xmodule.contentstore.content import StaticContent
from xmodule.contentstore.django import contentstore
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.mongo import MongoModuleStore
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, check_mongo_calls
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


@patch('django.http.HttpRequest', autospec=True)
def test_static_urls(mock_request):
    mock_request.build_absolute_uri = lambda url: 'http://' + url
    result = make_static_urls_absolute(mock_request, STATIC_SOURCE)
    assert_equals(result, '\"http:///static/file.png\"')


@patch('static_replace.staticfiles_storage', autospec=True)
def test_storage_url_exists(mock_storage):
    mock_storage.exists.return_value = True
    mock_storage.url.return_value = '/static/file.png'

    assert_equals('"/static/file.png"', replace_static_urls(STATIC_SOURCE, DATA_DIRECTORY))
    mock_storage.exists.assert_called_once_with('file.png')
    mock_storage.url.assert_called_once_with('file.png')


@patch('static_replace.staticfiles_storage', autospec=True)
def test_storage_url_not_exists(mock_storage):
    mock_storage.exists.return_value = False
    mock_storage.url.return_value = '/static/data_dir/file.png'

    assert_equals('"/static/data_dir/file.png"', replace_static_urls(STATIC_SOURCE, DATA_DIRECTORY))
    mock_storage.exists.assert_called_once_with('file.png')
    mock_storage.url.assert_called_once_with('data_dir/file.png')


@patch('static_replace.StaticContent', autospec=True)
@patch('static_replace.modulestore', autospec=True)
@patch('static_replace.AssetBaseUrlConfig.get_base_url')
@patch('static_replace.AssetExcludedExtensionsConfig.get_excluded_extensions')
def test_mongo_filestore(mock_get_excluded_extensions, mock_get_base_url, mock_modulestore, mock_static_content):

    mock_modulestore.return_value = Mock(MongoModuleStore)
    mock_static_content.get_canonicalized_asset_path.return_value = "c4x://mock_url"
    mock_get_base_url.return_value = u''
    mock_get_excluded_extensions.return_value = ['foobar']

    # No namespace => no change to path
    assert_equals('"/static/data_dir/file.png"', replace_static_urls(STATIC_SOURCE, DATA_DIRECTORY))

    # Namespace => content url
    assert_equals(
        '"' + mock_static_content.get_canonicalized_asset_path.return_value + '"',
        replace_static_urls(STATIC_SOURCE, DATA_DIRECTORY, course_id=COURSE_KEY)
    )

    mock_static_content.get_canonicalized_asset_path.assert_called_once_with(COURSE_KEY, 'file.png', u'', ['foobar'])


@patch('static_replace.settings', autospec=True)
@patch('static_replace.modulestore', autospec=True)
@patch('static_replace.staticfiles_storage', autospec=True)
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


@patch('static_replace.staticfiles_storage', autospec=True)
@patch('static_replace.modulestore', autospec=True)
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


@ddt.ddt
class CanonicalContentTest(SharedModuleStoreTestCase):
    """
    Tests the generation of canonical asset URLs for different types
    of assets: c4x-style, opaque key style, locked, unlocked, CDN
    set, CDN not set, etc.
    """

    def setUp(self):
        super(CanonicalContentTest, self).setUp()

    @classmethod
    def setUpClass(cls):
        cls.courses = {}

        super(CanonicalContentTest, cls).setUpClass()

        names_and_prefixes = [(ModuleStoreEnum.Type.split, 'split'), (ModuleStoreEnum.Type.mongo, 'old')]
        for store, prefix in names_and_prefixes:
            with cls.store.default_store(store):
                cls.courses[prefix] = CourseFactory.create(org='a', course='b', run=prefix)

                # Create an unlocked image.
                unlock_content = cls.create_image(prefix, (32, 32), 'blue', '{}_unlock.png')

                # Create a locked image.
                lock_content = cls.create_image(prefix, (32, 32), 'green', '{}_lock.png', locked=True)

                # Create a thumbnail of the images.
                contentstore().generate_thumbnail(unlock_content, dimensions=(16, 16))
                contentstore().generate_thumbnail(lock_content, dimensions=(16, 16))

                # Create an unlocked image in a subdirectory.
                cls.create_image(prefix, (1, 1), 'red', 'special/{}_unlock.png')

                # Create a locked image in a subdirectory.
                cls.create_image(prefix, (1, 1), 'yellow', 'special/{}_lock.png', locked=True)

                # Create an unlocked image with funky characters in the name.
                cls.create_image(prefix, (1, 1), 'black', 'weird {}_unlock.png')
                cls.create_image(prefix, (1, 1), 'black', 'special/weird {}_unlock.png')

                # Create an HTML file to test extension exclusion, and create a control file.
                cls.create_arbitrary_content(prefix, '{}_not_excluded.htm')
                cls.create_arbitrary_content(prefix, '{}_excluded.html')
                cls.create_arbitrary_content(prefix, 'special/{}_not_excluded.htm')
                cls.create_arbitrary_content(prefix, 'special/{}_excluded.html')

    @classmethod
    def create_image(cls, prefix, dimensions, color, name, locked=False):
        """
        Creates an image.

        Args:
            prefix: the prefix to use e.g. split vs mongo
            dimensions: tuple of (width, height)
            color: the background color of the image
            name: the name of the image; can be a format string
            locked: whether or not the asset should be locked

        Returns:
            StaticContent: the StaticContent object for the created image
        """
        new_image = Image.new('RGB', dimensions, color)
        new_buf = StringIO()
        new_image.save(new_buf, format='png')
        new_buf.seek(0)
        new_name = name.format(prefix)
        new_key = StaticContent.compute_location(cls.courses[prefix].id, new_name)
        new_content = StaticContent(new_key, new_name, 'image/png', new_buf.getvalue(), locked=locked)
        contentstore().save(new_content)

        return new_content

    @classmethod
    def create_arbitrary_content(cls, prefix, name, locked=False):
        """
        Creates an arbitrary piece of content with a fixed body, for when content doesn't matter.

        Args:
            prefix: the prefix to use e.g. split vs mongo
            name: the name of the content; can be a format string
            locked: whether or not the asset should be locked

        Returns:
            StaticContent: the StaticContent object for the created content

        """
        new_buf = StringIO('testingggggggggggg')
        new_name = name.format(prefix)
        new_key = StaticContent.compute_location(cls.courses[prefix].id, new_name)
        new_content = StaticContent(new_key, new_name, 'application/octet-stream', new_buf.getvalue(), locked=locked)
        contentstore().save(new_content)

        return new_content

    @ddt.data(
        # No leading slash.
        (u'', u'{prfx}_unlock.png', u'/{asset}@{prfx}_unlock.png', 1),
        (u'', u'{prfx}_lock.png', u'/{asset}@{prfx}_lock.png', 1),
        (u'', u'weird {prfx}_unlock.png', u'/{asset}@weird_{prfx}_unlock.png', 1),
        (u'', u'{prfx}_excluded.html', u'/{asset}@{prfx}_excluded.html', 1),
        (u'', u'{prfx}_not_excluded.htm', u'/{asset}@{prfx}_not_excluded.htm', 1),
        (u'dev', u'{prfx}_unlock.png', u'//dev/{asset}@{prfx}_unlock.png', 1),
        (u'dev', u'{prfx}_lock.png', u'/{asset}@{prfx}_lock.png', 1),
        (u'dev', u'weird {prfx}_unlock.png', u'//dev/{asset}@weird_{prfx}_unlock.png', 1),
        (u'dev', u'{prfx}_excluded.html', u'/{asset}@{prfx}_excluded.html', 1),
        (u'dev', u'{prfx}_not_excluded.htm', u'//dev/{asset}@{prfx}_not_excluded.htm', 1),
        # No leading slash with subdirectory.  This ensures we properly substitute slashes.
        (u'', u'special/{prfx}_unlock.png', u'/{asset}@special_{prfx}_unlock.png', 1),
        (u'', u'special/{prfx}_lock.png', u'/{asset}@special_{prfx}_lock.png', 1),
        (u'', u'special/weird {prfx}_unlock.png', u'/{asset}@special_weird_{prfx}_unlock.png', 1),
        (u'', u'special/{prfx}_excluded.html', u'/{asset}@special_{prfx}_excluded.html', 1),
        (u'', u'special/{prfx}_not_excluded.htm', u'/{asset}@special_{prfx}_not_excluded.htm', 1),
        (u'dev', u'special/{prfx}_unlock.png', u'//dev/{asset}@special_{prfx}_unlock.png', 1),
        (u'dev', u'special/{prfx}_lock.png', u'/{asset}@special_{prfx}_lock.png', 1),
        (u'dev', u'special/weird {prfx}_unlock.png', u'//dev/{asset}@special_weird_{prfx}_unlock.png', 1),
        (u'dev', u'special/{prfx}_excluded.html', u'/{asset}@special_{prfx}_excluded.html', 1),
        (u'dev', u'special/{prfx}_not_excluded.htm', u'//dev/{asset}@special_{prfx}_not_excluded.htm', 1),
        # Leading slash.
        (u'', u'/{prfx}_unlock.png', u'/{asset}@{prfx}_unlock.png', 1),
        (u'', u'/{prfx}_lock.png', u'/{asset}@{prfx}_lock.png', 1),
        (u'', u'/weird {prfx}_unlock.png', u'/{asset}@weird_{prfx}_unlock.png', 1),
        (u'', u'/{prfx}_excluded.html', u'/{asset}@{prfx}_excluded.html', 1),
        (u'', u'/{prfx}_not_excluded.htm', u'/{asset}@{prfx}_not_excluded.htm', 1),
        (u'dev', u'/{prfx}_unlock.png', u'//dev/{asset}@{prfx}_unlock.png', 1),
        (u'dev', u'/{prfx}_lock.png', u'/{asset}@{prfx}_lock.png', 1),
        (u'dev', u'/weird {prfx}_unlock.png', u'//dev/{asset}@weird_{prfx}_unlock.png', 1),
        (u'dev', u'/{prfx}_excluded.html', u'/{asset}@{prfx}_excluded.html', 1),
        (u'dev', u'/{prfx}_not_excluded.htm', u'//dev/{asset}@{prfx}_not_excluded.htm', 1),
        # Leading slash with subdirectory.  This ensures we properly substitute slashes.
        (u'', u'/special/{prfx}_unlock.png', u'/{asset}@special_{prfx}_unlock.png', 1),
        (u'', u'/special/{prfx}_lock.png', u'/{asset}@special_{prfx}_lock.png', 1),
        (u'', u'/special/weird {prfx}_unlock.png', u'/{asset}@special_weird_{prfx}_unlock.png', 1),
        (u'', u'/special/{prfx}_excluded.html', u'/{asset}@special_{prfx}_excluded.html', 1),
        (u'', u'/special/{prfx}_not_excluded.htm', u'/{asset}@special_{prfx}_not_excluded.htm', 1),
        (u'dev', u'/special/{prfx}_unlock.png', u'//dev/{asset}@special_{prfx}_unlock.png', 1),
        (u'dev', u'/special/{prfx}_lock.png', u'/{asset}@special_{prfx}_lock.png', 1),
        (u'dev', u'/special/weird {prfx}_unlock.png', u'//dev/{asset}@special_weird_{prfx}_unlock.png', 1),
        (u'dev', u'/special/{prfx}_excluded.html', u'/{asset}@special_{prfx}_excluded.html', 1),
        (u'dev', u'/special/{prfx}_not_excluded.htm', u'//dev/{asset}@special_{prfx}_not_excluded.htm', 1),
        # Static path.
        (u'', u'/static/{prfx}_unlock.png', u'/{asset}@{prfx}_unlock.png', 1),
        (u'', u'/static/{prfx}_lock.png', u'/{asset}@{prfx}_lock.png', 1),
        (u'', u'/static/weird {prfx}_unlock.png', u'/{asset}@weird_{prfx}_unlock.png', 1),
        (u'', u'/static/{prfx}_excluded.html', u'/{asset}@{prfx}_excluded.html', 1),
        (u'', u'/static/{prfx}_not_excluded.htm', u'/{asset}@{prfx}_not_excluded.htm', 1),
        (u'dev', u'/static/{prfx}_unlock.png', u'//dev/{asset}@{prfx}_unlock.png', 1),
        (u'dev', u'/static/{prfx}_lock.png', u'/{asset}@{prfx}_lock.png', 1),
        (u'dev', u'/static/weird {prfx}_unlock.png', u'//dev/{asset}@weird_{prfx}_unlock.png', 1),
        (u'dev', u'/static/{prfx}_excluded.html', u'/{asset}@{prfx}_excluded.html', 1),
        (u'dev', u'/static/{prfx}_not_excluded.htm', u'//dev/{asset}@{prfx}_not_excluded.htm', 1),
        # Static path with subdirectory.  This ensures we properly substitute slashes.
        (u'', u'/static/special/{prfx}_unlock.png', u'/{asset}@special_{prfx}_unlock.png', 1),
        (u'', u'/static/special/{prfx}_lock.png', u'/{asset}@special_{prfx}_lock.png', 1),
        (u'', u'/static/special/weird {prfx}_unlock.png', u'/{asset}@special_weird_{prfx}_unlock.png', 1),
        (u'', u'/static/special/{prfx}_excluded.html', u'/{asset}@special_{prfx}_excluded.html', 1),
        (u'', u'/static/special/{prfx}_not_excluded.htm', u'/{asset}@special_{prfx}_not_excluded.htm', 1),
        (u'dev', u'/static/special/{prfx}_unlock.png', u'//dev/{asset}@special_{prfx}_unlock.png', 1),
        (u'dev', u'/static/special/{prfx}_lock.png', u'/{asset}@special_{prfx}_lock.png', 1),
        (u'dev', u'/static/special/weird {prfx}_unlock.png', u'//dev/{asset}@special_weird_{prfx}_unlock.png', 1),
        (u'dev', u'/static/special/{prfx}_excluded.html', u'/{asset}@special_{prfx}_excluded.html', 1),
        (u'dev', u'/static/special/{prfx}_not_excluded.htm', u'//dev/{asset}@special_{prfx}_not_excluded.htm', 1),
        # Static path with query parameter.
        (
            u'',
            u'/static/{prfx}_unlock.png?foo=/static/{prfx}_lock.png',
            u'/{asset}@{prfx}_unlock.png?foo={encoded_asset}{prfx}_lock.png',
            2
        ),
        (
            u'',
            u'/static/{prfx}_lock.png?foo=/static/{prfx}_unlock.png',
            u'/{asset}@{prfx}_lock.png?foo={encoded_asset}{prfx}_unlock.png',
            2
        ),
        (
            u'',
            u'/static/{prfx}_excluded.html?foo=/static/{prfx}_excluded.html',
            u'/{asset}@{prfx}_excluded.html?foo={encoded_asset}{prfx}_excluded.html',
            2
        ),
        (
            u'',
            u'/static/{prfx}_excluded.html?foo=/static/{prfx}_not_excluded.htm',
            u'/{asset}@{prfx}_excluded.html?foo={encoded_asset}{prfx}_not_excluded.htm',
            2
        ),
        (
            u'',
            u'/static/{prfx}_not_excluded.htm?foo=/static/{prfx}_excluded.html',
            u'/{asset}@{prfx}_not_excluded.htm?foo={encoded_asset}{prfx}_excluded.html',
            2
        ),
        (
            u'',
            u'/static/{prfx}_not_excluded.htm?foo=/static/{prfx}_not_excluded.htm',
            u'/{asset}@{prfx}_not_excluded.htm?foo={encoded_asset}{prfx}_not_excluded.htm',
            2
        ),
        (
            u'dev',
            u'/static/{prfx}_unlock.png?foo=/static/{prfx}_lock.png',
            u'//dev/{asset}@{prfx}_unlock.png?foo={encoded_asset}{prfx}_lock.png',
            2
        ),
        (
            u'dev',
            u'/static/{prfx}_lock.png?foo=/static/{prfx}_unlock.png',
            u'/{asset}@{prfx}_lock.png?foo={encoded_base_url}{encoded_asset}{prfx}_unlock.png',
            2
        ),
        (
            u'dev',
            u'/static/{prfx}_excluded.html?foo=/static/{prfx}_excluded.html',
            u'/{asset}@{prfx}_excluded.html?foo={encoded_asset}{prfx}_excluded.html',
            2
        ),
        (
            u'dev',
            u'/static/{prfx}_excluded.html?foo=/static/{prfx}_not_excluded.htm',
            u'/{asset}@{prfx}_excluded.html?foo={encoded_base_url}{encoded_asset}{prfx}_not_excluded.htm',
            2
        ),
        (
            u'dev',
            u'/static/{prfx}_not_excluded.htm?foo=/static/{prfx}_excluded.html',
            u'//dev/{asset}@{prfx}_not_excluded.htm?foo={encoded_asset}{prfx}_excluded.html',
            2
        ),
        (
            u'dev',
            u'/static/{prfx}_not_excluded.htm?foo=/static/{prfx}_not_excluded.htm',
            u'//dev/{asset}@{prfx}_not_excluded.htm?foo={encoded_base_url}{encoded_asset}{prfx}_not_excluded.htm',
            2
        ),
        # Already asset key.
        (u'', u'/{asset}@{prfx}_unlock.png', u'/{asset}@{prfx}_unlock.png', 1),
        (u'', u'/{asset}@{prfx}_lock.png', u'/{asset}@{prfx}_lock.png', 1),
        (u'', u'/{asset}@weird_{prfx}_unlock.png', u'/{asset}@weird_{prfx}_unlock.png', 1),
        (u'', u'/{asset}@{prfx}_excluded.html', u'/{asset}@{prfx}_excluded.html', 1),
        (u'', u'/{asset}@{prfx}_not_excluded.htm', u'/{asset}@{prfx}_not_excluded.htm', 1),
        (u'dev', u'/{asset}@{prfx}_unlock.png', u'//dev/{asset}@{prfx}_unlock.png', 1),
        (u'dev', u'/{asset}@{prfx}_lock.png', u'/{asset}@{prfx}_lock.png', 1),
        (u'dev', u'/{asset}@weird_{prfx}_unlock.png', u'//dev/{asset}@weird_{prfx}_unlock.png', 1),
        (u'dev', u'/{asset}@{prfx}_excluded.html', u'/{asset}@{prfx}_excluded.html', 1),
        (u'dev', u'/{asset}@{prfx}_not_excluded.htm', u'//dev/{asset}@{prfx}_not_excluded.htm', 1),
        # Old, c4x-style path.
        (u'', u'/{c4x}/{prfx}_unlock.png', u'/{c4x}/{prfx}_unlock.png', 1),
        (u'', u'/{c4x}/{prfx}_lock.png', u'/{c4x}/{prfx}_lock.png', 1),
        (u'', u'/{c4x}/weird_{prfx}_lock.png', u'/{c4x}/weird_{prfx}_lock.png', 1),
        (u'', u'/{c4x}/{prfx}_excluded.html', u'/{c4x}/{prfx}_excluded.html', 1),
        (u'', u'/{c4x}/{prfx}_not_excluded.htm', u'/{c4x}/{prfx}_not_excluded.htm', 1),
        (u'dev', u'/{c4x}/{prfx}_unlock.png', u'/{c4x}/{prfx}_unlock.png', 1),
        (u'dev', u'/{c4x}/{prfx}_lock.png', u'/{c4x}/{prfx}_lock.png', 1),
        (u'dev', u'/{c4x}/weird_{prfx}_unlock.png', u'/{c4x}/weird_{prfx}_unlock.png', 1),
        (u'dev', u'/{c4x}/{prfx}_excluded.html', u'/{c4x}/{prfx}_excluded.html', 1),
        (u'dev', u'/{c4x}/{prfx}_not_excluded.htm', u'/{c4x}/{prfx}_not_excluded.htm', 1),
        # Thumbnails.
        (u'', u'/{th_key}@{prfx}_unlock-{th_ext}', u'/{th_key}@{prfx}_unlock-{th_ext}', 1),
        (u'', u'/{th_key}@{prfx}_lock-{th_ext}', u'/{th_key}@{prfx}_lock-{th_ext}', 1),
        (u'dev', u'/{th_key}@{prfx}_unlock-{th_ext}', u'//dev/{th_key}@{prfx}_unlock-{th_ext}', 1),
        (u'dev', u'/{th_key}@{prfx}_lock-{th_ext}', u'//dev/{th_key}@{prfx}_lock-{th_ext}', 1),
    )
    @ddt.unpack
    def test_canonical_asset_path_with_new_style_assets(self, base_url, start, expected, mongo_calls):
        exts = ['.html', '.tm']
        prefix = 'split'
        encoded_base_url = quote_plus('//' + base_url)
        c4x = 'c4x/a/b/asset'
        asset_key = 'asset-v1:a+b+{}+type@asset+block'.format(prefix)
        encoded_asset_key = quote_plus('/asset-v1:a+b+{}+type@asset+block@'.format(prefix))
        th_key = 'asset-v1:a+b+{}+type@thumbnail+block'.format(prefix)
        th_ext = 'png-16x16.jpg'

        start = start.format(
            prfx=prefix,
            c4x=c4x,
            asset=asset_key,
            encoded_base_url=encoded_base_url,
            encoded_asset=encoded_asset_key,
            th_key=th_key,
            th_ext=th_ext
        )
        expected = expected.format(
            prfx=prefix,
            c4x=c4x,
            asset=asset_key,
            encoded_base_url=encoded_base_url,
            encoded_asset=encoded_asset_key,
            th_key=th_key,
            th_ext=th_ext
        )

        with check_mongo_calls(mongo_calls):
            asset_path = StaticContent.get_canonicalized_asset_path(self.courses[prefix].id, start, base_url, exts)
            self.assertEqual(asset_path, expected)

    @ddt.data(
        # No leading slash.
        (u'', u'{prfx}_unlock.png', u'/{c4x}/{prfx}_unlock.png', 1),
        (u'', u'{prfx}_lock.png', u'/{c4x}/{prfx}_lock.png', 1),
        (u'', u'weird {prfx}_unlock.png', u'/{c4x}/weird_{prfx}_unlock.png', 1),
        (u'', u'{prfx}_excluded.html', u'/{c4x}/{prfx}_excluded.html', 1),
        (u'', u'{prfx}_not_excluded.htm', u'/{c4x}/{prfx}_not_excluded.htm', 1),
        (u'dev', u'{prfx}_unlock.png', u'//dev/{c4x}/{prfx}_unlock.png', 1),
        (u'dev', u'{prfx}_lock.png', u'/{c4x}/{prfx}_lock.png', 1),
        (u'dev', u'weird {prfx}_unlock.png', u'//dev/{c4x}/weird_{prfx}_unlock.png', 1),
        (u'dev', u'{prfx}_excluded.html', u'/{c4x}/{prfx}_excluded.html', 1),
        (u'dev', u'{prfx}_not_excluded.htm', u'//dev/{c4x}/{prfx}_not_excluded.htm', 1),
        # No leading slash with subdirectory.  This ensures we probably substitute slashes.
        (u'', u'special/{prfx}_unlock.png', u'/{c4x}/special_{prfx}_unlock.png', 1),
        (u'', u'special/{prfx}_lock.png', u'/{c4x}/special_{prfx}_lock.png', 1),
        (u'', u'special/weird {prfx}_unlock.png', u'/{c4x}/special_weird_{prfx}_unlock.png', 1),
        (u'', u'special/{prfx}_excluded.html', u'/{c4x}/special_{prfx}_excluded.html', 1),
        (u'', u'special/{prfx}_not_excluded.htm', u'/{c4x}/special_{prfx}_not_excluded.htm', 1),
        (u'dev', u'special/{prfx}_unlock.png', u'//dev/{c4x}/special_{prfx}_unlock.png', 1),
        (u'dev', u'special/{prfx}_lock.png', u'/{c4x}/special_{prfx}_lock.png', 1),
        (u'dev', u'special/weird {prfx}_unlock.png', u'//dev/{c4x}/special_weird_{prfx}_unlock.png', 1),
        (u'dev', u'special/{prfx}_excluded.html', u'/{c4x}/special_{prfx}_excluded.html', 1),
        (u'dev', u'special/{prfx}_not_excluded.htm', u'//dev/{c4x}/special_{prfx}_not_excluded.htm', 1),
        # Leading slash.
        (u'', u'/{prfx}_unlock.png', u'/{c4x}/{prfx}_unlock.png', 1),
        (u'', u'/{prfx}_lock.png', u'/{c4x}/{prfx}_lock.png', 1),
        (u'', u'/weird {prfx}_unlock.png', u'/{c4x}/weird_{prfx}_unlock.png', 1),
        (u'', u'/{prfx}_excluded.html', u'/{c4x}/{prfx}_excluded.html', 1),
        (u'', u'/{prfx}_not_excluded.htm', u'/{c4x}/{prfx}_not_excluded.htm', 1),
        (u'dev', u'/{prfx}_unlock.png', u'//dev/{c4x}/{prfx}_unlock.png', 1),
        (u'dev', u'/{prfx}_lock.png', u'/{c4x}/{prfx}_lock.png', 1),
        (u'dev', u'/weird {prfx}_unlock.png', u'//dev/{c4x}/weird_{prfx}_unlock.png', 1),
        (u'dev', u'/{prfx}_excluded.html', u'/{c4x}/{prfx}_excluded.html', 1),
        (u'dev', u'/{prfx}_not_excluded.htm', u'//dev/{c4x}/{prfx}_not_excluded.htm', 1),
        # Leading slash with subdirectory. This ensures we properly substitute slashes.
        (u'', u'/special/{prfx}_unlock.png', u'/{c4x}/special_{prfx}_unlock.png', 1),
        (u'', u'/special/{prfx}_lock.png', u'/{c4x}/special_{prfx}_lock.png', 1),
        (u'', u'/special/weird {prfx}_unlock.png', u'/{c4x}/special_weird_{prfx}_unlock.png', 1),
        (u'', u'/special/{prfx}_excluded.html', u'/{c4x}/special_{prfx}_excluded.html', 1),
        (u'', u'/special/{prfx}_not_excluded.htm', u'/{c4x}/special_{prfx}_not_excluded.htm', 1),
        (u'dev', u'/special/{prfx}_unlock.png', u'//dev/{c4x}/special_{prfx}_unlock.png', 1),
        (u'dev', u'/special/{prfx}_lock.png', u'/{c4x}/special_{prfx}_lock.png', 1),
        (u'dev', u'/special/weird {prfx}_unlock.png', u'//dev/{c4x}/special_weird_{prfx}_unlock.png', 1),
        (u'dev', u'/special/{prfx}_excluded.html', u'/{c4x}/special_{prfx}_excluded.html', 1),
        (u'dev', u'/special/{prfx}_not_excluded.htm', u'//dev/{c4x}/special_{prfx}_not_excluded.htm', 1),
        # Static path.
        (u'', u'/static/{prfx}_unlock.png', u'/{c4x}/{prfx}_unlock.png', 1),
        (u'', u'/static/{prfx}_lock.png', u'/{c4x}/{prfx}_lock.png', 1),
        (u'', u'/static/weird {prfx}_unlock.png', u'/{c4x}/weird_{prfx}_unlock.png', 1),
        (u'', u'/static/{prfx}_excluded.html', u'/{c4x}/{prfx}_excluded.html', 1),
        (u'', u'/static/{prfx}_not_excluded.htm', u'/{c4x}/{prfx}_not_excluded.htm', 1),
        (u'dev', u'/static/{prfx}_unlock.png', u'//dev/{c4x}/{prfx}_unlock.png', 1),
        (u'dev', u'/static/{prfx}_lock.png', u'/{c4x}/{prfx}_lock.png', 1),
        (u'dev', u'/static/weird {prfx}_unlock.png', u'//dev/{c4x}/weird_{prfx}_unlock.png', 1),
        (u'dev', u'/static/{prfx}_excluded.html', u'/{c4x}/{prfx}_excluded.html', 1),
        (u'dev', u'/static/{prfx}_not_excluded.htm', u'//dev/{c4x}/{prfx}_not_excluded.htm', 1),
        # Static path with subdirectory.  This ensures we properly substitute slashes.
        (u'', u'/static/special/{prfx}_unlock.png', u'/{c4x}/special_{prfx}_unlock.png', 1),
        (u'', u'/static/special/{prfx}_lock.png', u'/{c4x}/special_{prfx}_lock.png', 1),
        (u'', u'/static/special/weird {prfx}_unlock.png', u'/{c4x}/special_weird_{prfx}_unlock.png', 1),
        (u'', u'/static/special/{prfx}_excluded.html', u'/{c4x}/special_{prfx}_excluded.html', 1),
        (u'', u'/static/special/{prfx}_not_excluded.htm', u'/{c4x}/special_{prfx}_not_excluded.htm', 1),
        (u'dev', u'/static/special/{prfx}_unlock.png', u'//dev/{c4x}/special_{prfx}_unlock.png', 1),
        (u'dev', u'/static/special/{prfx}_lock.png', u'/{c4x}/special_{prfx}_lock.png', 1),
        (u'dev', u'/static/special/weird {prfx}_unlock.png', u'//dev/{c4x}/special_weird_{prfx}_unlock.png', 1),
        (u'dev', u'/static/special/{prfx}_excluded.html', u'/{c4x}/special_{prfx}_excluded.html', 1),
        (u'dev', u'/static/special/{prfx}_not_excluded.htm', u'//dev/{c4x}/special_{prfx}_not_excluded.htm', 1),
        # Static path with query parameter.
        (
            u'',
            u'/static/{prfx}_unlock.png?foo=/static/{prfx}_lock.png',
            u'/{c4x}/{prfx}_unlock.png?foo={encoded_c4x}{prfx}_lock.png',
            2
        ),
        (
            u'',
            u'/static/{prfx}_lock.png?foo=/static/{prfx}_unlock.png',
            u'/{c4x}/{prfx}_lock.png?foo={encoded_c4x}{prfx}_unlock.png',
            2
        ),
        (
            u'',
            u'/static/{prfx}_excluded.html?foo=/static/{prfx}_excluded.html',
            u'/{c4x}/{prfx}_excluded.html?foo={encoded_c4x}{prfx}_excluded.html',
            2
        ),
        (
            u'',
            u'/static/{prfx}_excluded.html?foo=/static/{prfx}_not_excluded.htm',
            u'/{c4x}/{prfx}_excluded.html?foo={encoded_c4x}{prfx}_not_excluded.htm',
            2
        ),
        (
            u'',
            u'/static/{prfx}_not_excluded.htm?foo=/static/{prfx}_excluded.html',
            u'/{c4x}/{prfx}_not_excluded.htm?foo={encoded_c4x}{prfx}_excluded.html',
            2
        ),
        (
            u'',
            u'/static/{prfx}_not_excluded.htm?foo=/static/{prfx}_not_excluded.htm',
            u'/{c4x}/{prfx}_not_excluded.htm?foo={encoded_c4x}{prfx}_not_excluded.htm',
            2
        ),
        (
            u'dev',
            u'/static/{prfx}_unlock.png?foo=/static/{prfx}_lock.png',
            u'//dev/{c4x}/{prfx}_unlock.png?foo={encoded_c4x}{prfx}_lock.png',
            2
        ),
        (
            u'dev',
            u'/static/{prfx}_lock.png?foo=/static/{prfx}_unlock.png',
            u'/{c4x}/{prfx}_lock.png?foo={encoded_base_url}{encoded_c4x}{prfx}_unlock.png',
            2
        ),
        (
            u'dev',
            u'/static/{prfx}_excluded.html?foo=/static/{prfx}_excluded.html',
            u'/{c4x}/{prfx}_excluded.html?foo={encoded_c4x}{prfx}_excluded.html',
            2
        ),
        (
            u'dev',
            u'/static/{prfx}_excluded.html?foo=/static/{prfx}_not_excluded.htm',
            u'/{c4x}/{prfx}_excluded.html?foo={encoded_base_url}{encoded_c4x}{prfx}_not_excluded.htm',
            2
        ),
        (
            u'dev',
            u'/static/{prfx}_not_excluded.htm?foo=/static/{prfx}_excluded.html',
            u'//dev/{c4x}/{prfx}_not_excluded.htm?foo={encoded_c4x}{prfx}_excluded.html',
            2
        ),
        (
            u'dev',
            u'/static/{prfx}_not_excluded.htm?foo=/static/{prfx}_not_excluded.htm',
            u'//dev/{c4x}/{prfx}_not_excluded.htm?foo={encoded_base_url}{encoded_c4x}{prfx}_not_excluded.htm',
            2
        ),
        # Old, c4x-style path.
        (u'', u'/{c4x}/{prfx}_unlock.png', u'/{c4x}/{prfx}_unlock.png', 1),
        (u'', u'/{c4x}/{prfx}_lock.png', u'/{c4x}/{prfx}_lock.png', 1),
        (u'', u'/{c4x}/weird_{prfx}_lock.png', u'/{c4x}/weird_{prfx}_lock.png', 1),
        (u'', u'/{c4x}/{prfx}_excluded.html', u'/{c4x}/{prfx}_excluded.html', 1),
        (u'', u'/{c4x}/{prfx}_not_excluded.htm', u'/{c4x}/{prfx}_not_excluded.htm', 1),
        (u'dev', u'/{c4x}/{prfx}_unlock.png', u'//dev/{c4x}/{prfx}_unlock.png', 1),
        (u'dev', u'/{c4x}/{prfx}_lock.png', u'/{c4x}/{prfx}_lock.png', 1),
        (u'dev', u'/{c4x}/weird_{prfx}_unlock.png', u'//dev/{c4x}/weird_{prfx}_unlock.png', 1),
        (u'dev', u'/{c4x}/{prfx}_excluded.html', u'/{c4x}/{prfx}_excluded.html', 1),
        (u'dev', u'/{c4x}/{prfx}_not_excluded.htm', u'//dev/{c4x}/{prfx}_not_excluded.htm', 1),
    )
    @ddt.unpack
    def test_canonical_asset_path_with_c4x_style_assets(self, base_url, start, expected, mongo_calls):
        exts = ['.html', '.tm']
        prefix = 'old'
        c4x_block = 'c4x/a/b/asset'
        encoded_c4x_block = quote_plus('/' + c4x_block + '/')
        encoded_base_url = quote_plus('//' + base_url)

        start = start.format(
            prfx=prefix,
            encoded_base_url=encoded_base_url,
            c4x=c4x_block,
            encoded_c4x=encoded_c4x_block
        )
        expected = expected.format(
            prfx=prefix,
            encoded_base_url=encoded_base_url,
            c4x=c4x_block,
            encoded_c4x=encoded_c4x_block
        )

        with check_mongo_calls(mongo_calls):
            asset_path = StaticContent.get_canonicalized_asset_path(self.courses[prefix].id, start, base_url, exts)
            self.assertEqual(asset_path, expected)

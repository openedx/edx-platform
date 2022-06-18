"""
Tests of AssetLocators
"""
from unittest import TestCase

import ddt
import itertools  # pylint: disable=wrong-import-order

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import AssetKey, CourseKey
from opaque_keys.edx.locator import AssetLocator, CourseLocator


@ddt.ddt
class TestAssetLocators(TestCase):
    """
    Tests of :class:`AssetLocator`
    """

    @ddt.data(
        "/c4x/org/course/asset/path",
    )
    def test_deprecated_round_trip_asset_location(self, path):
        self.assertEqual(
            path,
            str(AssetKey.from_string(path)),
        )

    def test_map_into_course_asset_location(self):
        original_course = CourseKey.from_string('org/course/run')
        new_course = CourseKey.from_string('edX/toy/2012_Fall')
        loc = AssetLocator(original_course, 'asset', 'foo.bar')
        self.assertEqual(
            AssetLocator(new_course, 'asset', 'foo.bar', deprecated=True),
            loc.map_into_course(new_course)
        )

    def test_make_asset_key(self):
        course = CourseKey.from_string('org/course/run')
        self.assertEqual(
            AssetLocator(course, 'asset', 'foo.bar', deprecated=True),
            course.make_asset_key('asset', 'foo.bar')
        )

    @ddt.data(
        (AssetLocator, '_id.', 'c4x', (CourseLocator('org', 'course', 'run', 'rev', deprecated=True), 'ct', 'n')),
        (AssetLocator, '_id.', 'c4x', (CourseLocator('org', 'course', 'run', 'rev', deprecated=True), 'ct', None)),
    )
    @ddt.unpack
    def test_deprecated_son(self, key_cls, prefix, tag, source):
        source_key = key_cls(*source, deprecated=True)
        son = source_key.to_deprecated_son(prefix=prefix, tag=tag)
        self.assertEqual(
            son.keys(),
            [prefix + key for key in ('tag', 'org', 'course', 'category', 'name', 'revision')]
        )

        self.assertEqual(son[prefix + 'tag'], tag)
        self.assertEqual(son[prefix + 'category'], source_key.block_type)
        self.assertEqual(son[prefix + 'name'], source_key.block_id)

        self.assertEqual(son[prefix + 'org'], source_key.course_key.org)
        self.assertEqual(son[prefix + 'course'], source_key.course_key.course)
        self.assertEqual(son[prefix + 'revision'], source_key.course_key.branch)

    @ddt.data(
        (AssetKey.from_string('/c4x/o/c/ct/n'), 'run'),
        (AssetKey.from_string('/c4x/o/c/ct/n@v'), 'run'),
    )
    @ddt.unpack
    def test_roundtrip_deprecated_son(self, key, run):
        self.assertEqual(
            key.replace(course_key=key.course_key.replace(run=run)),
            key.__class__._from_deprecated_son(key.to_deprecated_son(), run)  # pylint: disable=protected-access
        )

    def test_old_charset(self):
        # merely not raising InvalidKeyError suffices
        AssetLocator(CourseLocator('a', 'b', 'c'), 'asset', 'subs_%20S2x5jhbWl_o.srt.sjson')
        AssetLocator(CourseLocator('a', 'b', 'c'), 'asset', 'subs_%20S2x5jhbWl_o.srt.sjson', deprecated=True)

    def test_replace(self):
        asset_key = AssetKey.from_string('/c4x/o/c/asset/path')
        self.assertEqual(
            'foo',
            asset_key.replace(path='foo').path
        )
        self.assertEqual(
            'bar',
            asset_key.replace(asset_type='bar').asset_type
        )

    def test_empty_path(self):
        """ Test InvalidKeyError when asset path is empty """
        with self.assertRaises(InvalidKeyError):
            CourseKey.from_string('course-locator:org+course+run').make_asset_key('asset', '')

        with self.assertRaises(InvalidKeyError):
            CourseKey.from_string('org/course/run').make_asset_key('asset', '')

    @ddt.data(
        "asset-v1:UOG+cs_34+Cs128+type@asset+block@subs_Introduction%20To%20New.srt.sjson",
        "asset-v1:UOG+cs_34+Cs128+type@asset+block@subs_Introduction~To~New.srt.sjson",
        "asset-v1:UOG+cs_34+Cs128+type@asset+block@subs_Introduction:To:New.srt.sjson",
        "asset-v1:UOG+cs_34+Cs128+type@asset+block@subs_Introduction-To-New.srt.sjson",
    )
    def test_asset_with_special_character(self, path):
        asset_locator = AssetKey.from_string(path)
        self.assertEqual(
            path,
            str(asset_locator),
        )

    @ddt.data(*itertools.product(
        (
            "asset-v1:UOG+cs_34+Cs128+type@asset+block@subs_Introduction_To_New.srt.sjson{}",
        ),
        ('\n', '\n\n', ' ', '   ', '   \n'),
    ))
    @ddt.unpack
    def test_asset_with_trailing_whitespace(self, path_fmt, whitespace):
        with self.assertRaises(InvalidKeyError):
            AssetKey.from_string(path_fmt.format(whitespace))

    @ddt.data(
        "asset-v1:UOG+cs_34+Cs128+type@asset",
        "asset-v1:UOG+cs_34+Cs128",
    )
    def test_asset_with_missing_parts(self, path):
        with self.assertRaises(InvalidKeyError):
            AssetKey.from_string(path)

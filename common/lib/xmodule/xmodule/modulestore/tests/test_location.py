"""
Thorough tests of the Location class
"""
import ddt

from unittest import TestCase
from opaque_keys import InvalidKeyError
from xmodule.modulestore.locations import Location, AssetLocation, SlashSeparatedCourseKey

# Pairs for testing the clean* functions.
# The first item in the tuple is the input string.
# The second item in the tuple is what the result of
# replacement should be.
GENERAL_PAIRS = [
    ('', ''),
    (' ', '_'),
    ('abc,', 'abc_'),
    ('ab    fg!@//\\aj', 'ab_fg_aj'),
    (u"ab\xA9", "ab_"),  # no unicode allowed for now
]


@ddt.ddt
class TestLocations(TestCase):
    """
    Tests of :class:`.Location`
    """
    @ddt.data(
        "org+course+run+category+name",
        "org+course+run+category+name@revision"
    )
    def test_string_roundtrip(self, url):
        self.assertEquals(url, Location._from_string(url)._to_string())  # pylint: disable=protected-access

    @ddt.data(
        "i4x://org/course/category/name",
        "i4x://org/course/category/name@revision"
    )
    def test_deprecated_roundtrip(self, url):
        course_id = SlashSeparatedCourseKey('org', 'course', 'run')
        self.assertEquals(
            url,
            course_id.make_usage_key_from_deprecated_string(url).to_deprecated_string()
        )

    @ddt.data(
        ((), {
            'org': 'org',
            'course': 'course',
            'run': 'run',
            'category': 'category',
            'name': 'name',
        }, 'org', 'course', 'run', 'category', 'name', None),
        ((), {
            'org': 'org',
            'course': 'course',
            'run': 'run',
            'category': 'category',
            'name': 'name:more_name',
        }, 'org', 'course', 'run', 'category', 'name:more_name', None),
        (['org', 'course', 'run', 'category', 'name'], {}, 'org', 'course', 'run', 'category', 'name', None),
    )
    @ddt.unpack
    def test_valid_locations(self, args, kwargs, org, course, run, category, name, revision):
        location = Location(*args, **kwargs)
        self.assertEquals(org, location.org)
        self.assertEquals(course, location.course)
        self.assertEquals(run, location.run)
        self.assertEquals(category, location.category)
        self.assertEquals(name, location.name)
        self.assertEquals(revision, location.revision)

    @ddt.data(
        (("foo",), {}),
        (["foo", "bar"], {}),
        (["foo", "bar", "baz", "blat/blat", "foo"], {}),
        (["foo", "bar", "baz", "blat", "foo/bar"], {}),
        (["foo", "bar", "baz", "blat:blat", "foo:bar"], {}),  # ':' ok in name, not in category
        (('org', 'course', 'run', 'category', 'name with spaces', 'revision'), {}),
        (('org', 'course', 'run', 'category', 'name/with/slashes', 'revision'), {}),
        (('org', 'course', 'run', 'category', 'name', u'\xae'), {}),
        (('org', 'course', 'run', 'category', u'\xae', 'revision'), {}),
        ((), {
            'tag': 'tag',
            'course': 'course',
            'category': 'category',
            'name': 'name@more_name',
            'org': 'org'
        }),
        ((), {
            'tag': 'tag',
            'course': 'course',
            'category': 'category',
            'name': 'name ',   # extra space
            'org': 'org'
        }),
    )
    @ddt.unpack
    def test_invalid_locations(self, *args, **kwargs):
        with self.assertRaises(TypeError):
            Location(*args, **kwargs)

    def test_equality(self):
        self.assertEquals(
            Location('tag', 'org', 'course', 'run', 'category', 'name'),
            Location('tag', 'org', 'course', 'run', 'category', 'name')
        )

        self.assertNotEquals(
            Location('tag', 'org', 'course', 'run', 'category', 'name1'),
            Location('tag', 'org', 'course', 'run', 'category', 'name')
        )

    @ddt.data(
        ('a:b', 'a_b'),  # no colons in non-name components
        ('a-b', 'a-b'),  # dashes ok
        ('a.b', 'a.b'),  # dot ok
        *GENERAL_PAIRS
    )
    def test_clean(self, pair):
        self.assertEquals(Location.clean(pair[0]), pair[1])

    @ddt.data(
        ('a:b', 'a:b'),  # colons ok in names
        ('a-b', 'a-b'),  # dashes ok in names
        ('a.b', 'a.b'),  # dot ok in names
        *GENERAL_PAIRS
    )
    def test_clean_for_url_name(self, pair):
        self.assertEquals(Location.clean_for_url_name(pair[0]), pair[1])

    @ddt.data(
        ("a:b", "a_b"),   # no colons for html use
        ("a-b", "a-b"),   # dashes ok (though need to be replaced in various use locations. ugh.)
        ('a.b', 'a_b'),   # no dots.
        *GENERAL_PAIRS
    )
    def test_clean_for_html(self, pair):
        self.assertEquals(Location.clean_for_html(pair[0]), pair[1])

    def test_html_id(self):
        loc = Location('org', 'course', 'run', 'cat', 'name:more_name', 'rev')
        self.assertEquals(loc.html_id(), "i4x-org-course-cat-name_more_name-rev")

    def test_replacement(self):
        # pylint: disable=protected-access

        self.assertEquals(
            Location('o', 'c', 'r', 'c', 'n', 'r').replace(name='new_name'),
            Location('o', 'c', 'r', 'c', 'new_name', 'r'),
        )

        with self.assertRaises(InvalidKeyError):
            Location('o', 'c', 'r', 'c', 'n', 'r').replace(name=u'name\xae')

    @ddt.data('org', 'course', 'category', 'name', 'revision')
    def test_immutable(self, attr):
        loc = Location('o', 'c', 'r', 'c', 'n', 'r')
        with self.assertRaises(AttributeError):
            setattr(loc, attr, attr)

    def test_map_into_course_location(self):
        loc = Location('org', 'course', 'run', 'cat', 'name:more_name', 'rev')
        course_key = SlashSeparatedCourseKey("edX", "toy", "2012_Fall")
        self.assertEquals(
            Location("edX", "toy", "2012_Fall", 'cat', 'name:more_name', 'rev'),
            loc.map_into_course(course_key)
        )

    def test_map_into_course_asset_location(self):
        loc = AssetLocation('org', 'course', 'run', 'asset', 'foo.bar')
        course_key = SlashSeparatedCourseKey("edX", "toy", "2012_Fall")
        self.assertEquals(
            AssetLocation("edX", "toy", "2012_Fall", 'asset', 'foo.bar'),
            loc.map_into_course(course_key)
        )

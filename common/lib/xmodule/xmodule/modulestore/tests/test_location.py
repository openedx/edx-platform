import ddt

from unittest import TestCase
from xmodule.modulestore import Location
from xmodule.modulestore.exceptions import InvalidLocationError

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
        "tag://org/course/category/name",
        "tag://org/course/category/name@revision"
    )
    def test_string_roundtrip(self, url):
        self.assertEquals(url, Location(url).url())
        self.assertEquals(url, str(Location(url)))

    @ddt.data(
        {
            'tag': 'tag',
            'course': 'course',
            'category': 'category',
            'name': 'name',
            'org': 'org'
        },
        {
            'tag': 'tag',
            'course': 'course',
            'category': 'category',
            'name': 'name:more_name',
            'org': 'org'
        },
        ['tag', 'org', 'course', 'category', 'name'],
        "tag://org/course/category/name",
        "tag://org/course/category/name@revision",
        u"tag://org/course/category/name",
        u"tag://org/course/category/name@revision",
    )
    def test_is_valid(self, loc):
        self.assertTrue(Location.is_valid(loc))

    @ddt.data(
        {
            'tag': 'tag',
            'course': 'course',
            'category': 'category',
            'name': 'name@more_name',
            'org': 'org'
        },
        {
            'tag': 'tag',
            'course': 'course',
            'category': 'category',
            'name': 'name ',   # extra space
            'org': 'org'
        },
        "foo",
        ["foo"],
        ["foo", "bar"],
        ["foo", "bar", "baz", "blat:blat", "foo:bar"],  # ':' ok in name, not in category
        "tag://org/course/category/name with spaces@revision",
        "tag://org/course/category/name/with/slashes@revision",
        u"tag://org/course/category/name\xae",  # No non-ascii characters for now
        u"tag://org/course/category\xae/name",  # No non-ascii characters for now
    )
    def test_is_invalid(self, loc):
        self.assertFalse(Location.is_valid(loc))

    def test_dict(self):
        input_dict = {
            'tag': 'tag',
            'course': 'course',
            'category': 'category',
            'name': 'name',
            'org': 'org'
        }

        self.assertEquals("tag://org/course/category/name", Location(input_dict).url())
        self.assertEquals(dict(revision=None, **input_dict), Location(input_dict).dict())

        input_dict['revision'] = 'revision'
        self.assertEquals("tag://org/course/category/name@revision", Location(input_dict).url())
        self.assertEquals(input_dict, Location(input_dict).dict())

    def test_list(self):
        input_list = ['tag', 'org', 'course', 'category', 'name']
        self.assertEquals("tag://org/course/category/name", Location(input_list).url())
        self.assertEquals(input_list + [None], Location(input_list).list())

        input_list.append('revision')
        self.assertEquals("tag://org/course/category/name@revision", Location(input_list).url())
        self.assertEquals(input_list, Location(input_list).list())

    def test_location(self):
        input_list = ['tag', 'org', 'course', 'category', 'name']
        self.assertEquals("tag://org/course/category/name", Location(Location(input_list)).url())

    def test_none(self):
        self.assertEquals([None] * 6, Location(None).list())

    @ddt.data(
        "foo",
        ["foo", "bar"],
        ["foo", "bar", "baz", "blat/blat", "foo"],
        ["foo", "bar", "baz", "blat", "foo/bar"],
        "tag://org/course/category/name with spaces@revision",
        "tag://org/course/category/name/revision",
    )
    def test_invalid_locations(self, loc):
        with self.assertRaises(InvalidLocationError):
            Location(loc)

    def test_equality(self):
        self.assertEquals(
            Location('tag', 'org', 'course', 'category', 'name'),
            Location('tag', 'org', 'course', 'category', 'name')
        )

        self.assertNotEquals(
            Location('tag', 'org', 'course', 'category', 'name1'),
            Location('tag', 'org', 'course', 'category', 'name')
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
        loc = Location("tag://org/course/cat/name:more_name@rev")
        self.assertEquals(loc.html_id(), "tag-org-course-cat-name_more_name-rev")

    def test_course_id(self):
        loc = Location('i4x', 'mitX', '103', 'course', 'test2')
        self.assertEquals('mitX/103/test2', loc.course_id)

        loc = Location('i4x', 'mitX', '103', '_not_a_course', 'test2')
        with self.assertRaises(InvalidLocationError):
            loc.course_id  # pylint: disable=pointless-statement

    def test_replacement(self):
        # pylint: disable=protected-access

        self.assertEquals(
            Location('t://o/c/c/n@r')._replace(name='new_name'),
            Location('t://o/c/c/new_name@r'),
        )

        with self.assertRaises(InvalidLocationError):
            Location('t://o/c/c/n@r')._replace(name=u'name\xae')

    @ddt.data('org', 'course', 'category', 'name', 'revision')
    def test_immutable(self, attr):
        loc = Location('t://o/c/c/n@r')
        with self.assertRaises(AttributeError):
            setattr(loc, attr, attr)

from nose.tools import assert_equals, assert_raises, assert_not_equals
from xmodule.modulestore import Location
from xmodule.modulestore.exceptions import InvalidLocationError


def check_string_roundtrip(url):
    assert_equals(url, Location(url).url())
    assert_equals(url, str(Location(url)))


def test_string_roundtrip():
    check_string_roundtrip("tag://org/course/category/name")
    check_string_roundtrip("tag://org/course/category/name@revision")


input_dict = {
    'tag': 'tag',
    'course': 'course',
    'category': 'category',
    'name': 'name',
    'org': 'org'
}


also_valid_dict = {
    'tag': 'tag',
    'course': 'course',
    'category': 'category',
    'name': 'name:more_name',
    'org': 'org'
}


input_list = ['tag', 'org', 'course', 'category', 'name']

input_str = "tag://org/course/category/name"
input_str_rev = "tag://org/course/category/name@revision"

valid = (input_list, input_dict, input_str, input_str_rev, also_valid_dict)

invalid_dict = {
    'tag': 'tag',
    'course': 'course',
    'category': 'category',
    'name': 'name@more_name',
    'org': 'org'
}

invalid_dict2 = {
    'tag': 'tag',
    'course': 'course',
    'category': 'category',
    'name': 'name ',   # extra space
    'org': 'org'
}

invalid = ("foo", ["foo"], ["foo", "bar"],
           ["foo", "bar", "baz", "blat:blat", "foo:bar"],  # ':' ok in name, not in category
           "tag://org/course/category/name with spaces@revision",
           "tag://org/course/category/name/with/slashes@revision",
           invalid_dict,
           invalid_dict2)

def test_is_valid():
    for v in valid:
        assert_equals(Location.is_valid(v), True)

    for v in invalid:
        assert_equals(Location.is_valid(v), False)

def test_dict():
    assert_equals("tag://org/course/category/name", Location(input_dict).url())
    assert_equals(dict(revision=None, **input_dict), Location(input_dict).dict())

    input_dict['revision'] = 'revision'
    assert_equals("tag://org/course/category/name@revision", Location(input_dict).url())
    assert_equals(input_dict, Location(input_dict).dict())

def test_list():
    assert_equals("tag://org/course/category/name", Location(input_list).url())
    assert_equals(input_list + [None], Location(input_list).list())

    input_list.append('revision')
    assert_equals("tag://org/course/category/name@revision", Location(input_list).url())
    assert_equals(input_list, Location(input_list).list())


def test_location():
    input_list = ['tag', 'org', 'course', 'category', 'name']
    assert_equals("tag://org/course/category/name", Location(Location(input_list)).url())


def test_none():
    assert_equals([None] * 6, Location(None).list())


def test_invalid_locations():
    assert_raises(InvalidLocationError, Location, "foo")
    assert_raises(InvalidLocationError, Location, ["foo", "bar"])
    assert_raises(InvalidLocationError, Location, ["foo", "bar", "baz", "blat/blat", "foo"])
    assert_raises(InvalidLocationError, Location, ["foo", "bar", "baz", "blat", "foo/bar"])
    assert_raises(InvalidLocationError, Location, "tag://org/course/category/name with spaces@revision")
    assert_raises(InvalidLocationError, Location, "tag://org/course/category/name/revision")


def test_equality():
    assert_equals(
        Location('tag', 'org', 'course', 'category', 'name'),
        Location('tag', 'org', 'course', 'category', 'name')
    )

    assert_not_equals(
        Location('tag', 'org', 'course', 'category', 'name1'),
        Location('tag', 'org', 'course', 'category', 'name')
    )

# All the cleaning functions should do the same thing with these
general_pairs = [ ('',''),
                  (' ', '_'),
                  ('abc,', 'abc_'),
                  ('ab    fg!@//\\aj', 'ab_fg_aj'),
                  (u"ab\xA9", "ab_"),  # no unicode allowed for now
                  ]

def test_clean():
    pairs = general_pairs + [
        ('a:b', 'a_b'),  # no colons in non-name components
        ('a-b', 'a-b'),  # dashes ok 
        ('a.b', 'a.b'),  # dot ok
        ]
    for input, output in pairs:
        assert_equals(Location.clean(input), output)


def test_clean_for_url_name():
    pairs = general_pairs + [
        ('a:b', 'a:b'),  # colons ok in names
        ('a-b', 'a-b'),  # dashes ok in names
        ('a.b', 'a.b'),  # dot ok in names
        ]
    for input, output in pairs:
        assert_equals(Location.clean_for_url_name(input), output)


def test_clean_for_html():
    pairs = general_pairs + [
              ("a:b", "a_b"),   # no colons for html use
              ("a-b", "a-b"),   # dashes ok (though need to be replaced in various use locations. ugh.)
              ('a.b', 'a_b'),   # no dots.
              ]
    for input, output in pairs:
        assert_equals(Location.clean_for_html(input), output)


def test_html_id():
    loc = Location("tag://org/course/cat/name:more_name@rev")
    assert_equals(loc.html_id(), "tag-org-course-cat-name_more_name-rev")

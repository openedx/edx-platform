from nose.tools import assert_equals, assert_raises
from keystore import Location
from keystore.exceptions import InvalidLocationError


def check_string_roundtrip(url):
    assert_equals(url, Location(url).url())
    assert_equals(url, str(Location(url)))


def test_string_roundtrip():
    check_string_roundtrip("tag://org/course/category/name")
    check_string_roundtrip("tag://org/course/category/name/revision")
    check_string_roundtrip("tag://org/course/category/name with spaces/revision")


def test_dict():
    input_dict = {
        'tag': 'tag',
        'course': 'course',
        'category': 'category',
        'name': 'name',
        'org': 'org'
    }
    assert_equals("tag://org/course/category/name", Location(input_dict).url())
    assert_equals(dict(revision=None, **input_dict), Location(input_dict).dict())

    input_dict['revision'] = 'revision'
    assert_equals("tag://org/course/category/name/revision", Location(input_dict).url())
    assert_equals(input_dict, Location(input_dict).dict())


def test_list():
    input_list = ['tag', 'org', 'course', 'category', 'name']
    assert_equals("tag://org/course/category/name", Location(input_list).url())
    assert_equals(input_list + [None], Location(input_list).list())

    input_list.append('revision')
    assert_equals("tag://org/course/category/name/revision", Location(input_list).url())
    assert_equals(input_list, Location(input_list).list())


def test_location():
    input_list = ['tag', 'org', 'course', 'category', 'name']
    assert_equals("tag://org/course/category/name", Location(Location(input_list)).url())


def test_invalid_locations():
    assert_raises(InvalidLocationError, Location, "foo")
    assert_raises(InvalidLocationError, Location, ["foo", "bar"])
    assert_raises(InvalidLocationError, Location, ["foo", "bar", "baz", "blat", "foo/bar"])
    assert_raises(InvalidLocationError, Location, None)

import re

URL_RE = re.compile(r'^edx://(.+)$', re.IGNORECASE)


def parse_url(string):
    """
    A url must begin with 'edx://' (case-insensitive match),
    followed by either a version_guid or a course_id.

    Examples:
        'edx://@0123FFFF'
        'edx://edu.mit.eecs.6002x'
        'edx://edu.mit.eecs.6002x;published'
        'edx://edu.mit.eecs.6002x;published#HW3'

    This returns None if string cannot be parsed.

    If it can be parsed as a version_guid, returns a dict
    with key 'version_guid' and the value,

    If it can be parsed as a course_id, returns a dict
    with keys 'id' and 'branch' (value of 'branch' may be None),

    """
    match = URL_RE.match(string)
    if not match:
        return None
    path = match.group(1)
    if path[0] == '@':
        return parse_guid(path[1:])
    return parse_course_id(path)


BLOCK_RE = re.compile(r'^\w+$', re.IGNORECASE)


def parse_block_ref(string):
    r"""
    A block_ref is a string of word_chars.

    <word_chars> matches one or more Unicode word characters; this includes most
    characters that can be part of a word in any language, as well as numbers
    and the underscore. (see definition of \w in python regular expressions,
    at http://docs.python.org/dev/library/re.html)

    If string is a block_ref, returns a dict with key 'block_ref' and the value,
    otherwise returns None.
    """
    if len(string) > 0 and BLOCK_RE.match(string):
        return {'block': string}
    return None


GUID_RE = re.compile(r'^(?P<version_guid>[A-F0-9]+)(#(?P<block>\w+))?$', re.IGNORECASE)


def parse_guid(string):
    """
    A version_guid is a string of hex digits (0-F).

    If string is a version_guid, returns a dict with key 'version_guid' and the value,
    otherwise returns None.
    """
    m = GUID_RE.match(string)
    if m is not None:
        return m.groupdict()
    else:
        return None


COURSE_ID_RE = re.compile(r'^(?P<id>(\w+)(\.\w+\w*)*)(;(?P<branch>\w+))?(#(?P<block>\w+))?$', re.IGNORECASE)


def parse_course_id(string):
    r"""

    A course_id has a main id component.
    There may also be an optional branch (;published or ;draft).
    There may also be an optional block (#HW3 or #Quiz2).

    Examples of valid course_ids:

      'edu.mit.eecs.6002x'
      'edu.mit.eecs.6002x;published'
      'edu.mit.eecs.6002x#HW3'
      'edu.mit.eecs.6002x;published#HW3'


    Syntax:

      course_id = main_id [; branch] [# block]

      main_id = name [. name]*

      branch = name

      block = name

      name = <word_chars>

    <word_chars> matches one or more Unicode word characters; this includes most
    characters that can be part of a word in any language, as well as numbers
    and the underscore. (see definition of \w in python regular expressions,
    at http://docs.python.org/dev/library/re.html)

    If string is a course_id, returns a dict with keys 'id', 'branch', and 'block'.
    Revision is optional: if missing returned_dict['branch'] is None.
    Block is optional: if missing returned_dict['block'] is None.
    Else returns None.
    """
    match = COURSE_ID_RE.match(string)
    if not match:
        return None
    return match.groupdict()

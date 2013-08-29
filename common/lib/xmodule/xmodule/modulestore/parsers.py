import re

# Prefix for the branch portion of a locator URL
BRANCH_PREFIX = "/branch/"
# Prefix for the block portion of a locator URL
BLOCK_PREFIX = "/block/"
# Prefix for the version portion of a locator URL, when it is preceded by a course ID
VERSION_PREFIX = "/version/"
# Prefix for version when it begins the URL (no course ID).
URL_VERSION_PREFIX = 'version/'

URL_RE = re.compile(r'^edx://(.+)$', re.IGNORECASE)


def parse_url(string):
    """
    A url must begin with 'edx://' (case-insensitive match),
    followed by either a version_guid or a course_id.

    Examples:
        'edx://version/0123FFFF'
        'edx://mit.eecs.6002x'
        'edx://mit.eecs.6002x;published'
        'edx://mit.eecs.6002x;published/block/HW3'
        'edx://mit.eecs.6002x;published/version/000eee12345/block/HW3'

    This returns None if string cannot be parsed.

    If it can be parsed as a version_guid with no preceding course_id, returns a dict
    with key 'version_guid' and the value,

    If it can be parsed as a course_id, returns a dict
    with key 'id' and optional keys 'branch' and 'version_guid'.

    """
    match = URL_RE.match(string)
    if not match:
        return None
    path = match.group(1)
    if path.startswith(URL_VERSION_PREFIX):
        return parse_guid(path[len(URL_VERSION_PREFIX):])
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


GUID_RE = re.compile(r'^(?P<version_guid>[A-F0-9]+)(' + BLOCK_PREFIX + '(?P<block>\w+))?$', re.IGNORECASE)


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


COURSE_ID_RE = re.compile(
    r'^(?P<id>(\w+)(\.\w+\w*)*)(' +
    BRANCH_PREFIX + '(?P<branch>\w+))?(' +
    VERSION_PREFIX + '(?P<version_guid>[A-F0-9]+))?(' +
    BLOCK_PREFIX + '(?P<block>\w+))?$', re.IGNORECASE
)


def parse_course_id(string):
    r"""

    A course_id has a main id component.
    There may also be an optional branch (/branch/published or /branch/draft).
    There may also be an optional version (/version/519665f6223ebd6980884f2b).
    There may also be an optional block (/block/HW3 or /block/Quiz2).

    Examples of valid course_ids:

      'mit.eecs.6002x'
      'mit.eecs.6002x/branch/published'
      'mit.eecs.6002x/block/HW3'
      'mit.eecs.6002x/branch/published/block/HW3'
      'mit.eecs.6002x/branch/published/version/519665f6223ebd6980884f2b/block/HW3'


    Syntax:

      course_id = main_id [/branch/ branch] [/version/ version ] [/block/ block]

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

import re

# Prefix for the branch portion of a locator URL
BRANCH_PREFIX = r"branch/"
# Prefix for the block portion of a locator URL
BLOCK_PREFIX = r"block/"
# Prefix for the version portion of a locator URL, when it is preceded by a course ID
VERSION_PREFIX = r"version/"

ALLOWED_ID_CHARS = r'[a-zA-Z0-9_\-~.]'

URL_RE_SOURCE = r"""
    (?P<tag>edx://)?
    ((?P<course_id>{ALLOWED_ID_CHARS}+)/?)?
    ({BRANCH_PREFIX}(?P<branch>{ALLOWED_ID_CHARS}+)/?)?
    ({VERSION_PREFIX}(?P<version_guid>[A-F0-9]+)/?)?
    ({BLOCK_PREFIX}(?P<block>{ALLOWED_ID_CHARS}+))?
    """.format(
        ALLOWED_ID_CHARS=ALLOWED_ID_CHARS, BRANCH_PREFIX=BRANCH_PREFIX,
        VERSION_PREFIX=VERSION_PREFIX, BLOCK_PREFIX=BLOCK_PREFIX
    )

URL_RE = re.compile('^' + URL_RE_SOURCE + '$', re.IGNORECASE | re.VERBOSE)


def parse_url(string, tag_optional=False):
    """
    A url usually begins with 'edx://' (case-insensitive match),
    followed by either a version_guid or a course_id. If tag_optional, then
    the url does not have to start with the tag and edx will be assumed.

    Examples:
        'edx://version/0123FFFF'
        'edx://mit.eecs.6002x'
        'edx://mit.eecs.6002x/branch/published'
        'edx://mit.eecs.6002x/branch/published/block/HW3'
        'edx://mit.eecs.6002x/branch/published/version/000eee12345/block/HW3'

    This returns None if string cannot be parsed.

    If it can be parsed as a version_guid with no preceding course_id, returns a dict
    with key 'version_guid' and the value,

    If it can be parsed as a course_id, returns a dict
    with key 'id' and optional keys 'branch' and 'version_guid'.

    """
    match = URL_RE.match(string)
    if not match:
        return None
    matched_dict = match.groupdict()
    if matched_dict['tag'] is None and not tag_optional:
        return None
    return matched_dict


BLOCK_RE = re.compile(r'^' + ALLOWED_ID_CHARS + r'+$', re.IGNORECASE)


def parse_block_ref(string):
    r"""
    A block_ref is a string of url safe characters (see ALLOWED_ID_CHARS)

    If string is a block_ref, returns a dict with key 'block_ref' and the value,
    otherwise returns None.
    """
    if len(string) > 0 and BLOCK_RE.match(string):
        return {'block': string}
    return None


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

      name = ALLOWED_ID_CHARS

    If string is a course_id, returns a dict with keys 'id', 'branch', and 'block'.
    Revision is optional: if missing returned_dict['branch'] is None.
    Block is optional: if missing returned_dict['block'] is None.
    Else returns None.
    """
    match = URL_RE.match(string)
    if not match:
        return None
    return match.groupdict()

import re

URL_RE = re.compile('^edx://(.+)$')


def parse_url(string):
    """
    A url must begin with 'edx://' (case-insensitive match),
    followed by either a version_guid or a course_id.

    Examples:
        'edx://@0123FFFF'
        'edx://edu.mit.eecs.6002x'
        'edx://edu.mit.eecs.6002x;published'

    This returns None if string cannot be parsed.

    If it can be parsed as a version_guid, returns a dict
    with key 'version_guid' and the value,

    If it can be parsed as a course_id, returns a dict
    with keys 'id' and 'revision' (value of 'revision' may be None),
    
    """
    match = URL_RE.match(string.lower())
    if not match:
        return None
    path = match.group(1)
    if path[0]=='@':
        return parse_guid(path[1:])
    return parse_course_id(path)
    

GUID_RE = re.compile('^[a-fA-F0-9]+$')

def parse_guid(string):
    """
    A version_guid is a string of hex digits (0-F).
    
    If string is a version_guid, returns a dict with key 'version_guid' and the value,
    otherwise returns None.
    """
    if len(string)>0 and GUID_RE.match(string):
        return {'version_guid' : string}
    return None


COURSE_ID_RE = re.compile('^(?P<id>(\w+)(\.\w+\w*)*)(;(?P<revision>\w+))?$')
    
def parse_course_id(string):
    """

    A course_id has a main id component and an optional revision.
    Examples of valid course_ids:

      'edu.mit.eecs.6002x'
      'edu.mit.eecs.6002x;published'


    Syntax:

      course_id = main_id [; revision]
   
      main_id = name [. name]*

      revision = name

      name = <word_chars>

    <word_chars> matches one or more Unicode word characters; this includes most
    characters that can be part of a word in any language, as well as numbers
    and the underscore. (see definition of \w in python regular expressions,
    at http://docs.python.org/dev/library/re.html)

    If string is a course_id, returns a dict with keys 'id' and 'revision'.
    Revision is optional: if missing returned_dict['revision'] is None.
    Else returns None.
    """
    match = COURSE_ID_RE.match(string)
    if not match:
        return None
    return match.groupdict()

"""
Constants that are relevant to all of Open edX
"""
# These are standard regexes for pulling out info like course_ids, usage_ids, etc.
# They are used so that URLs with deprecated-format strings still work.
# Note: these intentionally greedily grab all chars up to the next slash includingny pluses
# DHM: I really wanted to ensure the separators were the same (+ or /) but all patts tried had
# too many inadvertent side effects :-(

COURSE_KEY_PATTERN = r'(?P<course_key_string>[^/+]+(/|\+)[^/+]+(/|\+)[^/?]+)'
COURSE_ID_PATTERN = COURSE_KEY_PATTERN.replace('course_key_string', 'course_id')
COURSE_KEY_REGEX = COURSE_KEY_PATTERN.replace('P<course_key_string>', ':')
COURSE_PUBLISHED = 'published'
COURSE_UNPUBLISHED = 'unpublished'

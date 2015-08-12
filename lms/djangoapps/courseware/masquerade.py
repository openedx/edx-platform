'''
---------------------------------------- Masquerade ----------------------------------------
Allow course staff to see a student or staff view of courseware.
Which kind of view has been selected is stored in the session state.
'''

import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST
from student.models import CourseEnrollment
from util.json_request import expect_json, JsonResponse

from opaque_keys.edx.keys import CourseKey
from xblock.fragment import Fragment
from xblock.runtime import KeyValueStore

log = logging.getLogger(__name__)

# The key used to store a user's course-level masquerade information in the Django session.
# The value is a dict from course keys to CourseMasquerade objects.
MASQUERADE_SETTINGS_KEY = 'masquerade_settings'

# The key used to store temporary XBlock field data in the Django session.  This is where field
# data is stored to avoid modifying the state of the user we are masquerading as.
MASQUERADE_DATA_KEY = 'masquerade_data'


class CourseMasquerade(object):
    """
    Masquerade settings for a particular course.
    """
    def __init__(self, course_key, role='student', user_partition_id=None, group_id=None, user_name=None):
        # All parameters to this function must be named identically to the corresponding attribute.
        # If you remove or rename an attribute, also update the __setstate__() method to migrate
        # old data from users' sessions.
        self.course_key = course_key
        self.role = role
        self.user_partition_id = user_partition_id
        self.group_id = group_id
        self.user_name = user_name

    def __setstate__(self, state):
        """
        Ensure that all attributes are initialised when unpickling CourseMasquerade objects.

        Users might still have CourseMasquerade objects from older versions of the code in their
        session.  These old objects might not have all attributes set, possibly resulting in
        AttributeErrors.
        """
        self.__init__(**state)


@require_POST
@login_required
@expect_json
def handle_ajax(request, course_key_string):
    """
    Handle AJAX posts to update the current user's masquerade for the specified course.
    The masquerade settings are stored in the Django session as a dict from course keys
    to CourseMasquerade objects.
    """
    course_key = CourseKey.from_string(course_key_string)
    masquerade_settings = request.session.get(MASQUERADE_SETTINGS_KEY, {})
    request_json = request.json
    role = request_json.get('role', 'student')
    group_id = request_json.get('group_id', None)
    user_partition_id = request_json.get('user_partition_id', None) if group_id is not None else None
    user_name = request_json.get('user_name', None)
    if user_name:
        users_in_course = CourseEnrollment.objects.users_enrolled_in(course_key)
        try:
            if '@' in user_name:
                user_name = users_in_course.get(email=user_name).username
            else:
                users_in_course.get(username=user_name)
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': _(
                    'There is no user with the username or email address {user_name} '
                    'enrolled in this course.'
                ).format(user_name=user_name)
            })
    masquerade_settings[course_key] = CourseMasquerade(
        course_key,
        role=role,
        user_partition_id=user_partition_id,
        group_id=group_id,
        user_name=user_name,
    )
    request.session[MASQUERADE_SETTINGS_KEY] = masquerade_settings
    return JsonResponse({'success': True})


def setup_masquerade(request, course_key, staff_access=False, reset_masquerade_data=False):
    """
    Sets up masquerading for the current user within the current request. The request's user is
    updated to have a 'masquerade_settings' attribute with the dict of all masqueraded settings if
    called from within a request context. The function then returns a pair (CourseMasquerade, User)
    with the masquerade settings for the specified course key or None if there isn't one, and the
    user we are masquerading as or request.user if masquerading as a specific user is not active.

    If the reset_masquerade_data flag is set, the field data stored in the session will be cleared.
    """
    if (
            request.user is None or
            not settings.FEATURES.get('ENABLE_MASQUERADE', False) or
            not staff_access
    ):
        return None, request.user
    if reset_masquerade_data:
        request.session.pop(MASQUERADE_DATA_KEY, None)
    masquerade_settings = request.session.setdefault(MASQUERADE_SETTINGS_KEY, {})
    # Store the masquerade settings on the user so it can be accessed without the request
    request.user.masquerade_settings = masquerade_settings
    course_masquerade = masquerade_settings.get(course_key, None)
    masquerade_user = None
    if course_masquerade and course_masquerade.user_name:
        try:
            masquerade_user = CourseEnrollment.objects.users_enrolled_in(course_key).get(
                username=course_masquerade.user_name
            )
        except User.DoesNotExist:
            # This can only happen if the user was unenrolled from the course since masquerading
            # was enabled.  We silently reset the masquerading configuration in this case.
            course_masquerade = None
            del masquerade_settings[course_key]
            request.session.modified = True
        else:
            # Store the masquerading settings on the masquerade_user as well, since this user will
            # be used in some places instead of request.user.
            masquerade_user.masquerade_settings = request.user.masquerade_settings
            masquerade_user.real_user = request.user
    return course_masquerade, masquerade_user or request.user


def get_course_masquerade(user, course_key):
    """
    Returns the masquerade for the current user for the specified course. If no masquerade has
    been installed, then a default no-op masquerade is returned.
    """
    masquerade_settings = getattr(user, 'masquerade_settings', {})
    return masquerade_settings.get(course_key, None)


def get_masquerade_role(user, course_key):
    """
    Returns the role that the user is masquerading as, or None if no masquerade is in effect.
    """
    course_masquerade = get_course_masquerade(user, course_key)
    return course_masquerade.role if course_masquerade else None


def is_masquerading_as_student(user, course_key):
    """
    Returns true if the user is a staff member masquerading as a student.
    """
    return get_masquerade_role(user, course_key) == 'student'


def is_masquerading_as_specific_student(user, course_key):  # pylint: disable=invalid-name
    """
    Returns whether the user is a staff member masquerading as a specific student.
    """
    course_masquerade = get_course_masquerade(user, course_key)
    return bool(course_masquerade and course_masquerade.user_name)


def get_masquerading_group_info(user, course_key):
    """
    If the user is masquerading as belonging to a group, then this method returns
    two values: the id of the group, and the id of the user partition that the group
    belongs to. If the user is not masquerading as a group, then None is returned.
    """
    course_masquerade = get_course_masquerade(user, course_key)
    if not course_masquerade:
        return None, None
    return course_masquerade.group_id, course_masquerade.user_partition_id


# Sentinel object to mark deleted objects in the session cache
_DELETED_SENTINEL = object()


class MasqueradingKeyValueStore(KeyValueStore):
    """
    A `KeyValueStore` to avoid affecting the user state when masquerading.

    This `KeyValueStore` wraps an underlying `KeyValueStore`.  Reads are forwarded to the underlying
    store, but writes go to a Django session (or other dictionary-like object).
    """
    def __init__(self, kvs, session):
        """
        Arguments:
          kvs: The KeyValueStore to wrap.
          session: The Django session used to store temporary data in.
        """
        self.kvs = kvs
        self.session = session
        self.session_data = session.setdefault(MASQUERADE_DATA_KEY, {})

    def _serialize_key(self, key):
        """
        Convert the key of Type KeyValueStore.Key to a string.

        Keys are not JSON-serializable, so we can't use them as keys for the Django session.
        The implementation is taken from cms/djangoapps/contentstore/views/session_kv_store.py.
        """
        return repr(tuple(key))

    def get(self, key):
        key_str = self._serialize_key(key)
        try:
            value = self.session_data[key_str]
        except KeyError:
            return self.kvs.get(key)
        else:
            if value is _DELETED_SENTINEL:
                raise KeyError(key_str)
            return value

    def set(self, key, value):
        self.session_data[self._serialize_key(key)] = value
        self.session.modified = True

    def delete(self, key):
        # We can't simply delete the key from the session, since it might still exist in the kvs,
        # which we are not allowed to modify, so we mark it as deleted by setting it to
        # _DELETED_SENTINEL in the session.
        self.set(key, _DELETED_SENTINEL)

    def has(self, key):
        try:
            value = self.session_data[self._serialize_key(key)]
        except KeyError:
            return self.kvs.has(key)
        else:
            return value != _DELETED_SENTINEL


def filter_displayed_blocks(block, unused_view, frag, unused_context):
    """
    A wrapper to only show XBlocks that set `show_in_read_only_mode` when masquerading as a specific user.

    We don't want to modify the state of the user we are masquerading as, so we can't show XBlocks
    that store information outside of the XBlock fields API.
    """
    if getattr(block, 'show_in_read_only_mode', False):
        return frag
    return Fragment(
        _(u'This type of component cannot be shown while viewing the course as a specific student.')
    )

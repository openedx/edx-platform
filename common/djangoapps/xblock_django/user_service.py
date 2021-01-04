"""
Support for converting a django user to an XBlock user
"""


from django.contrib.auth.models import User
from opaque_keys.edx.keys import CourseKey
from xblock.reference.user_service import UserService, XBlockUser

from openedx.core.djangoapps.external_user_ids.models import ExternalId
from openedx.core.djangoapps.user_api.preferences.api import get_user_preferences
from common.djangoapps.student.models import anonymous_id_for_user, get_user_by_username_or_email

ATTR_KEY_IS_AUTHENTICATED = 'edx-platform.is_authenticated'
ATTR_KEY_USER_ID = 'edx-platform.user_id'
ATTR_KEY_USERNAME = 'edx-platform.username'
ATTR_KEY_USER_IS_STAFF = 'edx-platform.user_is_staff'
ATTR_KEY_USER_PREFERENCES = 'edx-platform.user_preferences'
USER_PREFERENCES_WHITE_LIST = ['pref-lang', 'time_zone']


class DjangoXBlockUserService(UserService):
    """
    A user service that converts Django users to XBlockUser
    """
    def __init__(self, django_user, **kwargs):
        super(DjangoXBlockUserService, self).__init__(**kwargs)
        self._django_user = django_user
        if self._django_user:
            self._django_user.user_is_staff = kwargs.get('user_is_staff', False)

    def get_current_user(self):
        """
        Returns the currently-logged in user, as an instance of XBlockUser
        """
        return self._convert_django_user_to_xblock_user(self._django_user)

    def get_external_user_id(self, type_name):
        """
        Returns an external user id of the given type.
        Raises ValueError if the type doesn't exist.
        """
        external_id, _ = ExternalId.add_new_user_id(self._django_user, type_name)
        if not external_id:
            raise ValueError("External ID type: %s does not exist" % type_name)
        return str(external_id.external_user_id)

    def get_anonymous_user_id(self, username, course_id):
        """
        Get the anonymous user id for a user.

        Args:
            username(str): username of a user.
            course_id(str): course id of particular course.

        Returns:
            A unique anonymous_user_id for (user, course) pair.
            None for Non-staff users.
        """
        if not self.get_current_user().opt_attrs.get(ATTR_KEY_USER_IS_STAFF):
            return None

        try:
            user = get_user_by_username_or_email(username_or_email=username)
        except User.DoesNotExist:
            return None

        course_id = CourseKey.from_string(course_id)
        return anonymous_id_for_user(user=user, course_id=course_id, save=False)

    def _convert_django_user_to_xblock_user(self, django_user):
        """
        A function that returns an XBlockUser from the current Django request.user
        """
        xblock_user = XBlockUser(is_current_user=True)

        if django_user is not None and django_user.is_authenticated:
            # This full_name is dependent on edx-platform's profile implementation
            if hasattr(django_user, 'profile'):
                full_name = django_user.profile.name
            else:
                full_name = None
            xblock_user.full_name = full_name
            xblock_user.emails = [django_user.email]
            xblock_user.opt_attrs[ATTR_KEY_IS_AUTHENTICATED] = True
            xblock_user.opt_attrs[ATTR_KEY_USER_ID] = django_user.id
            xblock_user.opt_attrs[ATTR_KEY_USERNAME] = django_user.username
            xblock_user.opt_attrs[ATTR_KEY_USER_IS_STAFF] = django_user.user_is_staff
            user_preferences = get_user_preferences(django_user)
            xblock_user.opt_attrs[ATTR_KEY_USER_PREFERENCES] = {
                pref: user_preferences.get(pref)
                for pref in USER_PREFERENCES_WHITE_LIST
                if pref in user_preferences
            }
        else:
            xblock_user.opt_attrs[ATTR_KEY_IS_AUTHENTICATED] = False

        return xblock_user

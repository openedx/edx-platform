"""
Support for converting a django user to an XBlock user
"""
from xblock.reference.user_service import XBlockUser, UserService

ATTR_KEY_IS_AUTHENTICATED = 'edx-platform.is_authenticated'
ATTR_KEY_USER_ID = 'edx-platform.user_id'
ATTR_KEY_USERNAME = 'edx-platform.username'


class DjangoXBlockUserService(UserService):
    """
    A user service that converts Django users to XBlockUser
    """
    def __init__(self, django_user, **kwargs):
        super(DjangoXBlockUserService, self).__init__(**kwargs)
        self._django_user = django_user

    def get_current_user(self):
        """
        Returns the currently-logged in user, as an instance of XBlockUser
        """
        return self._convert_django_user_to_xblock_user(self._django_user)

    def _convert_django_user_to_xblock_user(self, django_user):
        """
        A function that returns an XBlockUser from the current Django request.user
        """
        xblock_user = XBlockUser(is_current_user=True)

        if django_user is not None and django_user.is_authenticated():
            # This full_name is dependent on edx-platform's profile implementation
            full_name = getattr(django_user.profile, 'name') if hasattr(django_user, 'profile') else None
            xblock_user.full_name = full_name
            xblock_user.emails = [django_user.email]
            xblock_user.opt_attrs[ATTR_KEY_IS_AUTHENTICATED] = True
            xblock_user.opt_attrs[ATTR_KEY_USER_ID] = django_user.id
            xblock_user.opt_attrs[ATTR_KEY_USERNAME] = django_user.username
        else:
            xblock_user.opt_attrs[ATTR_KEY_IS_AUTHENTICATED] = False

        return xblock_user

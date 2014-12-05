"""
Support for converting a django user to an XBlock user
"""
from xblock.reference.user_service import XBlockUser, UserService


class DjangoXBlockUserService(UserService):
    """
    A user service that converts django users to XBlockUser
    """
    def __init__(self, user, **kwargs):
        super(DjangoXBlockUserService, self).__init__(**kwargs)
        self._user = user

    def get_current_user(self):
        return self._convert_django_user_to_xblock_user(self._user)

    def _convert_django_user_to_xblock_user(self, user):
        """
        A function that returns an XBlockUser from the current django request.user
        """
        if user.is_authenticated():
            full_name = user.profile.name if hasattr(user, 'profile') else None
            return XBlockUser(
                is_authenticated=True,
                email=user.email,
                full_name=full_name,
                username=user.username,
                user_id=user.id,
            )
        else:
            return XBlockUser(is_authenticated=False)

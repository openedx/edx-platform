"""
Support for converting a django user to an XBlock user
"""
from xblock.reference.user_service import XBlockUser, UserService
from student.models import anonymous_id_for_user


def convert_django_user_to_xblock_user(user, course_id=None):
    """
    A function that returns an XBlockUser from the current django request.user
    """
    if user.is_authenticated():
        course_anon_id = anonymous_id_for_user(user, course_id)
        global_anon_id = anonymous_id_for_user(user, None)
        full_name = user.profile.name if hasattr(user, 'profile') else None
        return XBlockUser(
            is_authenticated=True,
            email=user.email,
            full_name=full_name,
            username=user.username,
            id=user.id,
            course_anon_id=course_anon_id,
            global_anon_id=global_anon_id,
        )
    else:
        return XBlockUser(is_authenticated=False)


class DjangoXBlockUserService(UserService):
    """
    A user service that converts django users to XBlockUser
    """
    def __init__(self, user, course_id=None, **kwargs):
        super(DjangoXBlockUserService, self).__init__(**kwargs)
        self._user = user
        self._course_id = course_id

    def get_current_user(self):
        return convert_django_user_to_xblock_user(self._user, self._course_id)

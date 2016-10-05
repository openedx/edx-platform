from django.contrib.auth import get_user_model
from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore.django import modulestore

from .registry import register_scope


class Constants(object):
    COURSE_SCOPE = "course"
    USER_SCOPE = "user"


class ScopeStrategy(object):
    def get_scope(self, scope_id):
        raise NotImplementedError()


@register_scope
class CourseScopeStrategy(ScopeStrategy):
    SCOPE_TYPE = Constants.COURSE_SCOPE

    def __init__(self, module_store):
        self._modulestore = module_store()

    def get_scope(self, scope_id):
        course_key = CourseKey.from_string(scope_id)
        return self._modulestore.get_course(course_key)


@register_scope
class UserScopeStrategy(ScopeStrategy):
    SCOPE_TYPE = Constants.USER_SCOPE

    def __init__(self, get_user_by_id):
        self._get_user_by_id = get_user_by_id

    def get_scope(self, scope_id):
        return self._get_user_by_id(scope_id)


class ScopeFactory(object):
    @classmethod
    def make_scope_strategy(cls, scope_type):
        # TODO: there will be more scopes, so this if .. elif .. else will likely grow beyond any sensible size
        if scope_type == Constants.COURSE_SCOPE:
            module_store = modulestore()
            return CourseScopeStrategy(module_store)
        elif scope_type == Constants.USER_SCOPE:
            user_model = get_user_model()
            get_user_by_id = lambda user_id: user_model.objects.get(pk=user_id)
            return UserScopeStrategy(get_user_by_id)

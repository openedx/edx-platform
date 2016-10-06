from django.contrib.auth import get_user_model
from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore.django import modulestore

from .registry import register_scope


class Constants(object):
    COURSE_SCOPE = "course"
    USER_SCOPE = "user"


class Scope(object):
    """
    Abstract class implementing base Scope interface.

    Having a base class will help extending Entitlements in future - as new Django apps are added, some may introduce
    new "scopeable" objects. It would be natural to provide scopes for that objects as part of the app that define them.
    """
    def get_scope(self, scope_id):
        """
        Returns an object an entitlement is scoped to.

        Different scopes have different scope IDs (i.e. DB table primary key value, course key, etc.), hence scope_id
        is stored (and passed into this method) as a string. This method is responsilbe to converting string scope_id
        to an actual ID and fetching an object from the storage.
        """
        raise NotImplementedError()


@register_scope
class CourseScope(Scope):
    """
    Course scope. Entitlements having this scope are applicable to an instance of a course.
    """
    SCOPE_TYPE = Constants.COURSE_SCOPE

    def __init__(self, module_store):
        self._modulestore = module_store()

    def get_scope(self, scope_id):
        """
        Returns a course entitlement is scoped to.
        :param str scope_id: serialized CourseKey
        :return: CourseModule
        """
        course_key = CourseKey.from_string(scope_id)
        return self._modulestore.get_course(course_key)


@register_scope
class UserScope(Scope):
    """
    User scope. Entitlements having this scope are applicable to one particular user.
    """
    SCOPE_TYPE = Constants.USER_SCOPE

    def __init__(self, get_user_by_id):
        self._get_user_by_id = get_user_by_id

    def get_scope(self, scope_id):
        """
        Returns a user entitlement is scoped to.
        :param str scope_id: serialized user ID (integer)
        :return: django.contrib.auth.models.User
        """
        return self._get_user_by_id(scope_id)


class ScopeFactory(object):
    """
    This class instantiates Scopes and implements factory method pattern

    Different scopes have different dependencies (i.e. modulestore, get_user_by_id method, etc.). This class
    is responsible for resolving this dependencies transparent to callers.
    """

    # TODO: the factory should allow registering factory methods for scopes, rather than use "static" resolution
    # Adding new scope in other app will require this method to be modified, hence introducing circular reference.
    # IDEA: make it part of `registry`???
    @classmethod
    def make_scope_strategy(cls, scope_type):
        """
        This method instantiates a Scope with all required dependencies.
        :param str scope_type: type of scope to instantiate
        :return: instance of Scope subclass
        """
        # TODO: there will be more scopes, so this if .. elif .. else will likely grow beyond any sensible size
        if scope_type == Constants.COURSE_SCOPE:
            module_store = modulestore()
            return CourseScope(module_store)
        elif scope_type == Constants.USER_SCOPE:
            user_model = get_user_model()
            get_user_by_id = lambda user_id: user_model.objects.get(pk=user_id)
            return UserScope(get_user_by_id)

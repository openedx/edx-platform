"""
User Tag Course Context.
"""
from xmodule.modulestore.django import modulestore
from .context import UserTagContext
from ..provider import UserTagProvider


class UserTagCourseContext(UserTagContext):
    """
    Class for Course context.
    """
    def __init__(self, course_key=None, course=None):
        if course:
            course_key = course.id
        elif not course_key:
            raise ValueError(u'Either course_key or course need to be provided.')

        self._course_key = course_key
        self._course = course

    @property
    def id(self):
        return self._course_key

    @property
    def course(self):
        """
        Returns and caches the course object.
        """
        if not self._course:
            self._course = modulestore().get_course(self._course_key)
        return self._course


class UserTagProviderCourseContext(UserTagProvider):
    """
    Helper class for UserTagProviders that only support
    the course context.
    """
    tag_type = None

    @classmethod
    def tags(cls, context=None, **kwargs):
        if not context or not isinstance(context, UserTagCourseContext):
            return []
        return cls.course_tags(context, **kwargs)

    @classmethod
    def get_users_for_tag(cls, tag, context=None, **kwargs):
        if not context or not isinstance(context, UserTagCourseContext):
            return []
        if not isinstance(tag, cls.tag_type) or context.id != tag.course_key:
            return []
        return cls.get_users_for_course_tag(tag, context, **kwargs)

    @classmethod
    def get_tags_for_user(cls, user, context=None, **kwargs):
        if not context or not isinstance(context, UserTagCourseContext):
            return []
        return cls.get_course_tags_for_user(user, context, **kwargs)

    @classmethod
    def course_tags(cls, course_context, **kwargs):
        """
        Returns tags for the given course_context.
        """
        raise NotImplementedError

    @classmethod
    def get_users_for_course_tag(cls, tag, course_context, **kwargs):
        """
        Returns users associated with the given tag within the
        given course_context.
        """
        raise NotImplementedError

    @classmethod
    def get_course_tags_for_user(cls, user, course_context, **kwargs):
        """
        Returns tags within the given course_context for the given user.
        """
        raise NotImplementedError

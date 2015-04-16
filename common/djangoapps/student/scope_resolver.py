"""
A User Scope Resolver that can be used by edx-notifications
"""

import logging

from edx_notifications.scopes import NotificationUserScopeResolver
from student.models import CourseEnrollment
from django.contrib.auth.models import User

from opaque_keys.edx.keys import CourseKey
from opaque_keys import InvalidKeyError
from opaque_keys.edx.locations import SlashSeparatedCourseKey

log = logging.getLogger(__name__)


class CourseEnrollmentsScopeResolver(NotificationUserScopeResolver):
    """
    Implementation of the NotificationUserScopeResolver abstract
    interface defined in edx-notifications.

    An instance of this class will be registered to handle
    scope_name = 'course_enrollments' during system startup.

    We will be passed in a course_id in the context
    and we must return a Django ORM resultset or None if
    we cannot match.
    """

    def resolve(self, scope_name, scope_context, instance_context):
        """
        The entry point to resolve a scope_name with a given scope_context
        """

        if scope_name != 'course_enrollments':
            # we can't resolve any other scopes
            return None

        if 'course_id' not in scope_context:
            # did not receive expected parameters
            return None

        course_id = scope_context['course_id']

        if not isinstance(course_id , CourseKey):
            try:
                course_key = CourseKey.from_string(course_id)
            except InvalidKeyError:
               course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
        else:
            course_key = course_id

        return CourseEnrollment.objects.values_list('user_id', flat=True).filter(
            is_active=1,
            course_id=course_key
        )


class NamespaceEnrollmentsScopeResolver(NotificationUserScopeResolver):
    """
    Implementation of the NotificationUserScopeResolver abstract
    interface defined in edx-notifications.

    We will be passed in a namespace (aka course_id) in the context
    and we must return a Django ORM resultset or None if
    we cannot match.
    """

    def resolve(self, scope_name, scope_context, instance_context):
        """
        The entry point to resolve a scope_name with a given scope_context
        """

        if scope_name != 'namespace_scope':
            # we can't resolve any other scopes
            return None

        if 'namespace' not in scope_context:
            # did not receive expected parameters
            return None

        course_id = scope_context['namespace']

        if not isinstance(course_id , CourseKey):
            try:
                course_key = CourseKey.from_string(course_id)
            except InvalidKeyError:
               course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
        else:
            course_key = course_id

        query = User.objects.select_related('courseenrollment')

        if 'fields' in scope_context:
            fields = []
            if scope_context['fields'].get('id'):
                fields.append('id')

            if scope_context['fields'].get('email'):
                fields.append('email')

            if scope_context['fields'].get('first_name'):
                fields.append('first_name')

            if scope_context['fields'].get('last_name'):
                fields.append('last_name')
        else:
            fields =['id', 'email', 'first_name', 'last_name']

        query = query.values(*fields)
        query = query.filter(
            courseenrollment__is_active=1,
            courseenrollment__course_id=course_key
        )
        return query


class StudentEmailScopeResolver(NotificationUserScopeResolver):
    """
    Implementation of the NotificationUserScopeResolver to
    take in a user_id and return that user's email address
    """

    def resolve(self, scope_name, scope_context, instance_context):
        """
        The entry point to resolve a scope_name with a given scope_context
        """

        if scope_name != 'user_email_resolver':
            # we can't resolve any other scopes
            return None

        user_id = scope_context.get('user_id')
        if not user_id:
            return None

        return User.objects.values_list('email', flat=True).filter(
            id=user_id
        )

"""
A namespace resolver for edx-notifications. This basically translates a namespace
into information about the namespace
"""

from xmodule.modulestore.django import modulestore
from student.scope_resolver import NamespaceEnrollmentsScopeResolver
from edx_notifications.namespaces import NotificationNamespaceResolver

from opaque_keys.edx.keys import CourseKey
from opaque_keys import InvalidKeyError
from opaque_keys.edx.locations import SlashSeparatedCourseKey


class CourseNamespaceResolver(NotificationNamespaceResolver):
    """
    An implementation of NotificationNamespaceResolver which treats
    namespaces as courses
    """

    def resolve(self, namespace, instance_context):
        """
        Namespace resolvers will return this information as a dict:

        {
            'namespace': <String> ,
            'display_name': <String representing a human readible name for the namespace>,
            'features': {
                'digests': <boolean, saying if namespace supports a digest>
            },
            'default_user_resolver': <pointer to a UserScopeResolver instance>
        }
        or None if the handler cannot resolve it
        """

        # namespace = course_id
        course_id = namespace

        if not isinstance(course_id, CourseKey):
            try:
                course_key = CourseKey.from_string(course_id)
            except InvalidKeyError:
                try:
                   course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
                except InvalidKeyError:
                    return None
        else:
            course_key = course_id

        course = modulestore().get_course(course_key)

        if not course:
            # not found, we can't resolve it
            return None

        # return expected results to caller per the interface contract
        return {
            'namespace': course_id,
            'display_name': course.display_name,
            'features': {
                'digests': course.has_started() and not course.has_ended(),
            },
            'default_user_resolver': NamespaceEnrollmentsScopeResolver(),
        }



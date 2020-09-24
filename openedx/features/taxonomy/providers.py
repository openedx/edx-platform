"""
Course metadata provider for taxonomy app.
"""
from taxonomy.providers import CourseMetadataProvider

from openedx.core.djangoapps.catalog.utils import get_courses_by_uuid


class DiscoveryCourseMetadataProvider(CourseMetadataProvider):
    """
    Discovery course metadata provider.
    """

    @staticmethod
    def get_courses(course_ids):
        """
        Get list of courses matching the given course UUIDs and return then in the form of a dict.
        """
        courses = get_courses_by_uuid(course_ids)

        return [{
            'uuid': course['uuid'],
            'key': course['key'],
            'title': course['title'],
            'short_description': course['short_description'],
            'full_description': course['full_description'],
        } for course in courses]

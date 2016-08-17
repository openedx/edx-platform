"""
This file contains the exception used in courseware access
"""
from django.http import Http404


class CoursewareAccessException(Http404):
    """
    Exception for courseware access errors
    """

    def __init__(self, access_response):
        super(CoursewareAccessException, self).__init__()
        self.access_response = access_response
        self.message = "Course not found."

    def to_json(self):
        """
        Creates a serializable JSON representation of an CoursewareAccessException.

        Returns:
            dict: JSON representation
        """
        return self.access_response.to_json()

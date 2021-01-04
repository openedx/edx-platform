"""
Common Purpose Errors
"""

from django.core.exceptions import ObjectDoesNotExist


class CourseNotFoundError(ObjectDoesNotExist):
    """
    Course was not found.
    """
    pass


class PageNotFoundError(ObjectDoesNotExist):
    """
    Page was not found. Used for paginated endpoint.
    """
    pass


class DiscussionNotFoundError(ObjectDoesNotExist):
    """
    Discussion Module was not found.
    """
    pass

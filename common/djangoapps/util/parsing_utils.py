"""
Utility function for some parsing stuff
"""
from xmodule.contentstore.content import StaticContent


def course_image_url(course):
    """
    Return url of course image.
    Args:
        course(CourseDescriptor) : The course id to retrieve course image url.
    Returns:
        Absolute url of course image.
    """
    loc = StaticContent.compute_location(course.id, course.course_image)
    url = StaticContent.serialize_asset_key_with_slash(loc)
    return url

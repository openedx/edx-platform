"""
Serializers for all Course Descriptor and Course About Descriptor related return objects.

"""
from xmodule.contentstore.content import StaticContent
from django.conf import settings

DATE_FORMAT = getattr(settings, 'API_DATE_FORMAT', '%Y-%m-%d')


def serialize_content(course_descriptor, about_descriptor):
    """
    Returns a serialized representation of the course_descriptor and about_descriptor
    Args:
        course_descriptor(CourseDescriptor) : course descriptor object
        about_descriptor(dict) : Dictionary of CourseAboutDescriptor objects
    return:
        serialize data for course information.
    """
    data = {
        'media': {},
        'display_name': getattr(course_descriptor, 'display_name', None),
        'course_number': course_descriptor.location.course,
        'course_id': None,
        'advertised_start': getattr(course_descriptor, 'advertised_start', None),
        'is_new': getattr(course_descriptor, 'is_new', None),
        'start': _formatted_datetime(course_descriptor, 'start'),
        'end': _formatted_datetime(course_descriptor, 'end'),
        'announcement': None,
    }
    data.update(about_descriptor)

    content_id = unicode(course_descriptor.id)
    data["course_id"] = unicode(content_id)
    if getattr(course_descriptor, 'course_image', False):
        data['media']['course_image'] = course_image_url(course_descriptor)

    announcement = getattr(course_descriptor, 'announcement', None)
    data["announcement"] = announcement.strftime(DATE_FORMAT) if announcement else None

    return data


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


def _formatted_datetime(course_descriptor, date_type):
    """
    Return formatted date.
    Args:
        course_descriptor(CourseDescriptor) : The CourseDescriptor Object.
        date_type (str) : Either start or end.
    Returns:
        formatted date or None .
    """
    course_date_ = getattr(course_descriptor, date_type, None)
    return course_date_.strftime(DATE_FORMAT) if course_date_ else None

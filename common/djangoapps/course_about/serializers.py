"""
Serializers for all Course Descriptor and Course About Descriptor related return objects.

"""
from xmodule.contentstore.content import StaticContent


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
        "course_id": unicode(course_descriptor.id),
        'display_name': getattr(course_descriptor, 'display_name', None),
        'course_number': course_descriptor.location.course,
        'course_id': None,
        'advertised_start': getattr(course_descriptor, 'advertised_start', None),
        'is_new': getattr(course_descriptor, 'is_new', None),
        'start': None,
        'end': None,
        'announcement': None,
        'effort': about_descriptor.get("effort", None)

    }
    if getattr(course_descriptor, 'course_image', False):
        data['media']['image'] = _course_image_url(course_descriptor)

    start = getattr(course_descriptor, 'start', None)
    end = getattr(course_descriptor, 'end', None)
    announcement = getattr(course_descriptor, 'announcement', None)

    data['start'] = start.strftime('%Y-%m-%d') if start else None
    data['end'] = end.strftime('%Y-%m-%d') if end else None
    data["announcement"] = announcement.strftime('%Y-%m-%d') if announcement else None

    return data


def _course_image_url(course):
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

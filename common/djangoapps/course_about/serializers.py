"""
Serializers for all Course Descriptor and Course About Descriptor related return objects.

"""
from util.parsing_utils import course_image_url
from django.conf import settings


def serialize_content(course_descriptor, about_descriptor):
    """Serialize the course descriptor and about descriptor

    Returns a serialized representation of the course_descriptor and about_descriptor

    Args:
        course_descriptor(CourseDescriptor) : course descriptor object
        about_descriptor(dict) : Dictionary of CourseAboutDescriptor objects

    Returns:
        Serializable  dictionary of course information.

    """
    date_format = getattr(settings, 'API_DATE_FORMAT', '%Y-%m-%d')
    data = dict({"media": {}})
    data['display_name'] = getattr(course_descriptor, 'display_name', None)
    start = getattr(course_descriptor, 'start', None)
    end = getattr(course_descriptor, 'end', None)
    announcement = getattr(course_descriptor, 'announcement', None)
    data['start'] = start.strftime(date_format) if start else None
    data['end'] = end.strftime(date_format) if end else None
    data["announcement"] = announcement.strftime(date_format) if announcement else None
    data['advertised_start'] = getattr(course_descriptor, 'advertised_start', None)
    data['is_new'] = getattr(course_descriptor, 'is_new', None)
    image_url = ''
    if hasattr(course_descriptor, 'course_image') and course_descriptor.course_image:
        image_url = course_image_url(course_descriptor)
    data['course_number'] = course_descriptor.location.course
    data['course_id'] = unicode(course_descriptor.id)
    data['media']['course_image'] = image_url
    # Following code is getting the course about descriptor information
    course_about_data = _course_about_serialize_content(about_descriptor)
    data.update(course_about_data)
    return data


def _course_about_serialize_content(about_descriptor):
    """Serialize the course about descriptor

    Returns a serialized representation of the about_descriptor

    Args:
        course_descriptor(dict) : dictionary of course descriptor object

    Returns:
        Serialize data for about descriptor.

    """
    data = dict()
    data["effort"] = about_descriptor.get("effort", None)
    return data

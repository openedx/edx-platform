"""
Serializers for all Course Descriptor and Course About Descriptor related return objects.

"""
from util.parsing_utils import parse_video_tag
from lms.djangoapps.courseware.courses import course_image_url


def _serialize_content(course_descriptor, about_descriptor):
    """
    Returns a serialized representation of the course_descriptor and about_descriptor
    Args:
        course_descriptor : course descriptor object

    return:
        serialize data for course information.
    """
    data = dict()
    data['display_name'] = getattr(course_descriptor, 'display_name', None)
    data['start'] = getattr(course_descriptor, 'start', None)
    data['end'] = getattr(course_descriptor, 'end', None)
    data["announcement"] = getattr(course_descriptor, 'announcement', None)
    data['advertised_start'] = getattr(course_descriptor, 'advertised_start', None)
    data['is_new'] = getattr(course_descriptor, 'is_new', None)

    image_url = ''
    if hasattr(course_descriptor, 'course_image') and course_descriptor.course_image:
        image_url = course_image_url(course_descriptor)

    content_id = unicode(course_descriptor.id)
    data['course_number'] = course_descriptor.location.course

    data['course_id'] = unicode(content_id)

    # Following code is getting the course about descriptor information

    course_about_data = _course_about_serialize_content(about_descriptor)

    data['media'] = {}
    data['media']['course_image'] = image_url
    data['media']['video'] = parse_video_tag(course_about_data["video"])
    data["effort"] = course_about_data["effort"]
    return data


def _course_about_serialize_content(about_descriptor):
    """
    Returns a serialized representation of the about_descriptor

    Args:
        course_descriptor : course descriptor object

    return:
        serialize data for about descriptor.
    """
    data = dict()
    data["video"] = about_descriptor.get("video", None)
    data["effort"] = about_descriptor.get("effort", None)
    return data



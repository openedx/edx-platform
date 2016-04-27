"""
Common utility functions related to courses.
"""
from django.conf import settings

from xmodule.assetstore.assetmgr import AssetManager
from xmodule.contentstore.content import StaticContent
from xmodule.contentstore.django import contentstore
from xmodule.modulestore.django import modulestore
from xmodule.modulestore import ModuleStoreEnum


def course_image_url(course):
    """Try to look up the image url for the course.  If it's not found,
    log an error and return the dead link"""
    if course.static_asset_path or modulestore().get_modulestore_type(course.id) == ModuleStoreEnum.Type.xml:
        # If we are a static course with the course_image attribute
        # set different than the default, return that path so that
        # courses can use custom course image paths, otherwise just
        # return the default static path.
        url = '/static/' + (course.static_asset_path or getattr(course, 'data_dir', ''))
        if hasattr(course, 'course_image') and course.course_image != course.fields['course_image'].default:
            url += '/' + course.course_image
        else:
            url += '/images/course_image.jpg'
    elif not course.course_image:
        # if course_image is empty, use the default image url from settings
        url = settings.STATIC_URL + settings.DEFAULT_COURSE_ABOUT_IMAGE_URL
    else:
        loc = StaticContent.compute_location(course.id, course.course_image)
        url = StaticContent.serialize_asset_key_with_slash(loc)

    return url


def create_course_image_thumbnail(course, dimensions):
    """Create a course image thumbnail and return the URL.

    - dimensions is a tuple of (width, height)
    """
    course_image_asset_key = StaticContent.compute_location(course.id, course.course_image)
    course_image = AssetManager.find(course_image_asset_key)  # a StaticContent obj

    _content, thumb_loc = contentstore().generate_thumbnail(course_image, dimensions=dimensions)

    return StaticContent.serialize_asset_key_with_slash(thumb_loc)

import jwt
from custom_settings.models import CustomSettings
from opaque_keys.edx.keys import CourseKey


def get_encoded_token(username, email, id):
    return jwt.encode({'id': id, 'username': username, 'email': email }, 'secret', algorithm='HS256')


def get_course_custom_settings(course_key):
    """ Return course custom settings object """
    if isinstance(course_key, str) or isinstance(course_key, unicode):
        course_key = CourseKey.from_string(course_key)

    return CustomSettings.objects.filter(id=course_key).first()

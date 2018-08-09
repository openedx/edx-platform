import jwt
from custom_settings.models import CustomSettings


def get_encoded_token(username, email, id):
    return jwt.encode({'id': id, 'username': username, 'email': email }, 'secret', algorithm='HS256')


def get_course_custom_settings(course_key):
    """ Return course custom settings object """
    return CustomSettings.objects.filter(id=course_key).first()

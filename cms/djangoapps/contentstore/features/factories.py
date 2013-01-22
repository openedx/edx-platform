import factory
from student.models import User, UserProfile, Registration
from datetime import datetime
import uuid

class UserProfileFactory(factory.Factory):
    FACTORY_FOR = UserProfile

    user = None
    name = 'Robot Studio'
    courseware = 'course.xml'

class RegistrationFactory(factory.Factory):
    FACTORY_FOR = Registration

    user = None
    activation_key = uuid.uuid4().hex

class UserFactory(factory.Factory):
    FACTORY_FOR = User

    username = 'robot-studio'
    email = 'robot+studio@edx.org'
    password = 'test'
    first_name = 'Robot'
    last_name = 'Studio'
    is_staff = False
    is_active = True
    is_superuser = False
    last_login = datetime.now()
    date_joined = datetime.now()
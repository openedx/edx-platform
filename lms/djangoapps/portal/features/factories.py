import factory
from student.models import User, UserProfile, Registration
from datetime import datetime
import uuid

class UserProfileFactory(factory.Factory):
    FACTORY_FOR = UserProfile

    user = None
    name = 'Jack Foo'
    level_of_education = None
    gender = 'm'
    mailing_address = None
    goals = 'World domination'

class RegistrationFactory(factory.Factory):
    FACTORY_FOR = Registration

    user = None
    activation_key = uuid.uuid4().hex

class UserFactory(factory.Factory):
    FACTORY_FOR = User

    username = 'robot'
    email = 'robot+test@edx.org'
    password = 'test'
    first_name = 'Robot'
    last_name = 'Test'
    is_staff = False
    is_active = True
    is_superuser = False
    last_login = datetime(2012, 1, 1)
    date_joined = datetime(2011, 1, 1)

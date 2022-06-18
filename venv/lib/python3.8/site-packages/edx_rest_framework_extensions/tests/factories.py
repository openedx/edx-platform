""" Test factories. """
import factory
from django.contrib.auth import get_user_model


PASSWORD = 'password'


class UserFactory(factory.DjangoModelFactory):
    """ User factory. """
    username = email = factory.Sequence(lambda n: f'user{n}')
    email = factory.Sequence(lambda n: f'user{n}@example.com')
    password = factory.PostGenerationMethodCall('set_password', PASSWORD)
    is_active = True
    is_superuser = False
    is_staff = False

    class Meta:
        model = get_user_model()

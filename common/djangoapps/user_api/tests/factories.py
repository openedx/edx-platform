from factory.django import DjangoModelFactory
from user_api.models import UserPreference


class UserPreferenceFactory(DjangoModelFactory):
    FACTORY_FOR = UserPreference

    user = None
    key = None
    value = "default test value"

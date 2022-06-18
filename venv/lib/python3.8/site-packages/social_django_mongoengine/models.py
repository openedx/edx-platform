"""
MongoEngine Django models for Social Auth.
Requires MongoEngine 0.8.6 or higher.
"""
from django.conf import settings

from mongoengine import Document, ReferenceField
from mongoengine.queryset import OperationError

from social_core.utils import setting_name, module_member
from social_mongoengine.storage import MongoengineUserMixin, \
                                       MongoengineAssociationMixin, \
                                       MongoengineNonceMixin, \
                                       MongoengineCodeMixin, \
                                       MongoenginePartialMixin, \
                                       BaseMongoengineStorage


UNUSABLE_PASSWORD = '!'  # Borrowed from django 1.4


def _get_user_model():
    """
    Get the User Document class user for MongoEngine authentication.

    Use the model defined in SOCIAL_AUTH_USER_MODEL if defined, or
    defaults to MongoEngine's configured user document class.
    """
    custom_model = getattr(settings, setting_name('USER_MODEL'), None)
    if custom_model:
        return module_member(custom_model)

    try:
        from django_mongoengine.mongo_auth.models import get_user_document
        return get_user_document()
    except ImportError:
        return module_member('mongoengine.django.auth.User')


USER_MODEL = _get_user_model()


class UserSocialAuth(Document, MongoengineUserMixin):
    """Social Auth association model"""
    user = ReferenceField(USER_MODEL)

    @classmethod
    def user_model(cls):
        return USER_MODEL


class Nonce(Document, MongoengineNonceMixin):
    """One use numbers"""
    pass


class Association(Document, MongoengineAssociationMixin):
    """OpenId account association"""
    pass


class Code(Document, MongoengineCodeMixin):
    """Mail validation single one time use code"""
    pass


class Partial(Document, MongoenginePartialMixin):
    """Partial pipeline data"""
    pass


class DjangoStorage(BaseMongoengineStorage):
    user = UserSocialAuth
    nonce = Nonce
    association = Association
    code = Code
    partial = Partial

    @classmethod
    def is_integrity_error(cls, exception):
        return exception.__class__ is OperationError and \
               'E11000' in exception.message

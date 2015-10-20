"""
Monkey patch implementation for a python_social_auth class that is not Django 1.8-compatible.
Remove once the module fully supports Django 1.8!
"""

import six
from django.db import transaction
import social.storage.django_orm


def patch():
    """
    Monkey-patch the DjangoUserMixin class.
    """
    class PatchedDjangoUserMixin(social.storage.django_orm.DjangoUserMixin):

        # Save the super of a DjangoUserMixin instance for later use.
        # TODO: I don't think this is correct! set_extra_data() needs to call the super
        # TODO: of the actual instance, instead of the super of the object constructed here.
        # TODO: But if I don't do this and use it in the overridden set_extra_data(), an
        # TODO: infinite recursive loop happens when the method is called.
        super_inst = super(social.storage.django_orm.DjangoUserMixin, social.storage.django_orm.DjangoUserMixin())

        @classmethod
        def create_social_auth(cls, user, uid, provider):
            if not isinstance(uid, six.string_types):
                uid = str(uid)
            # If the create fails below due to an IntegrityError, ensure that the transaction
            # stays undamaged by wrapping the create in an atomic.
            with transaction.atomic():
                social_auth = cls.objects.create(user=user, uid=uid, provider=provider)
            return social_auth

        def set_extra_data(self, extra_data=None):
            if self.super_inst.set_extra_data(extra_data):
                self.save()

    # Monkey-patch the social DjangoUserMixin so that it is Django 1.8-compatible.
    social.storage.django_orm.DjangoUserMixin = PatchedDjangoUserMixin

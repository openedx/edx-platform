# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _

# Create your models here.


class UserRoleResource(models.Model):
    """ """
    ENTERPRISE_CUSTOMER = 'enterprise_customer'
    RESOURCE_CHOICES = (
        (ENTERPRISE_CUSTOMER, _('Enterprise Customer')),
    )

    ROLE_CHOICES = (
        ('enterprise_learner', _('Enterprise Learner')),
        ('enterprise_admin', _('Enterprise Admin')),
    )
    user_email = models.EmailField(db_index=True)
    role = models.CharField(max_length=255, db_index=True, choices=ROLE_CHOICES)
    object_type = models.CharField(
        max_length=255,
        choices=RESOURCE_CHOICES,
        db_index=True,
    )
    object_key = models.CharField(max_length=255, db_index=True)

    def __str__(self):
        """
        Return human-readable string representation.
        """
        return '{user}:{role}:{object_type}:{object_key}'.format(
            user=self.user_email,
            role=self.role,
            object_type=self.object_type,
            object_key=self.object_key,
        )

    def __repr__(self):
        """
        Return uniquely identifying string representation.
        """
        return self.__str__()

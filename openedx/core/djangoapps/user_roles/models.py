# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.db import models


class UserRole(models.Model):
    """
    System wide roles, configurable per OpenedX instance.
    """
    name = models.CharField(max_length=255, db_index=True)

    class Meta:
        abstract = True

    def __str__(self):
        """
        Return human-readable string representation.
        """
        return self.name


class UserRoleAssignment(models.Model):
    """
    System wide user roles for users.
    """
    user = models.ForeignKey(User, db_index=True, on_delete=models.CASCADE)
    role = models.ForeignKey(UserRole, db_index=True, on_delete=models.CASCADE)

    class Meta:
        abstract = True

    def __str__(self):
        """
        Return human-readable string representation.
        """
        return '{user}:{role}'.format(
            user=self.user.id,
            role=self.role.name,
        )

    def __repr__(self):
        """
        Return uniquely identifying string representation.
        """
        return self.__str__()

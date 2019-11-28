"""
Django models for the groups REST API

The "Group" model is part of Django's standard authentication framework, but we
need to augment it with a "Group Admin" model in order to know which users (if
any) have permission to edit any given group.
"""
from __future__ import absolute_import, division, print_function, unicode_literals

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import models
from django.utils.encoding import python_2_unicode_compatible

User = get_user_model()


@python_2_unicode_compatible
class GroupAdminUser(models.Model):
    """
    Represents a user that has been given permission to administer a group.

    Any user in the group can see the group's membership using the group API,
    but only these "Group Admin" users can add/remove users in the group, or
    delete the group via the REST API.
    """
    group = models.ForeignKey(Group, null=False, blank=False)
    user = models.ForeignKey(User, null=True, blank=True)

    def __str__(self):
        return "<GroupAdmin: {username} administers {group}>".format(  # xss-lint: disable=python-wrap-html
            username=self.user.username,
            group=self.group.name,
        )

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.contrib.auth.models import Group, User
from .models import UserRoleResource

# Register your models here.


@admin.register(UserRoleResource)
class UserRoleResourceAdmin(admin.ModelAdmin):
    """
    Django admin model for EnterpriseCustomerUser.
    """

    class Meta(object):
        model = UserRoleResource

    def save_model(self, request, obj, form, change):
        """ """
        user = User.objects.get(email=obj.user_email)
        group, _ = Group.objects.get_or_create(name=obj.role)
        user.groups.add(group)
        user.save()

        super(UserRoleResourceAdmin, self).save_model(request, obj, form, change)

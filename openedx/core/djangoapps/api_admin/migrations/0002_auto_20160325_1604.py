# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


API_GROUP_NAME = 'API Access Request Approvers'


def add_api_access_group(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    ApiAccessRequest = apps.get_model('api_admin', 'ApiAccessRequest')

    group, __ = Group.objects.get_or_create(name=API_GROUP_NAME)
    api_content_type = ContentType.objects.get_for_model(ApiAccessRequest)
    group.permissions = Permission.objects.filter(content_type=api_content_type)
    group.save()


def delete_api_access_group(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name=API_GROUP_NAME).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('api_admin', '0001_initial'),
        ('contenttypes', '0002_remove_content_type_name')
    ]

    operations = [
        migrations.RunPython(add_api_access_group, delete_api_access_group)
    ]

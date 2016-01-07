# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

from django.conf import settings
from django.contrib.auth.models import User


def add_service_user(apps, schema_editor):
    """Add service user."""
    user = User.objects.create(username=settings.CREDENTIALS_SERVICE_USERNAME)
    user.set_unusable_password()
    user.save()


def remove_service_user(apps, schema_editor):
    """Remove service user."""
    User.objects.get(username=settings.CREDENTIALS_SERVICE_USERNAME).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('credentials', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(add_service_user, remove_service_user)
        ]

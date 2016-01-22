# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging

from django.db import migrations

from django.conf import settings
from django.contrib.auth.models import User


logger = logging.getLogger(__name__)


def add_service_user(apps, schema_editor):
    """Add service user."""
    user, created = User.objects.get_or_create(username=settings.CREDENTIALS_SERVICE_USERNAME)
    if created:
        user.is_staff = True
        user.set_unusable_password()
        user.save()


def remove_service_user(apps, schema_editor):
    """Remove service user."""
    try:
        User.objects.get(username=settings.CREDENTIALS_SERVICE_USERNAME).delete()
    except Exception:  # pylint: disable=broad-except
        logger.exception('Unexpected error while attempting to delete credentials service user.')
        logger.warning('This service user account may need cleanup, but migrations can safely continue.')


class Migration(migrations.Migration):

    dependencies = [
        ('credentials', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(add_service_user, remove_service_user),
    ]

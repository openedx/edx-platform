# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models, migrations


USERNAME = settings.ECOMMERCE_SERVICE_WORKER_USERNAME
EMAIL = USERNAME + '@fake.email'

def forwards(apps, schema_editor):
    """Add the service user."""
    user, created = User.objects.get_or_create(username=USERNAME, email=EMAIL)
    if created:
        user.set_unusable_password()
        user.save()

def backwards(apps, schema_editor):
    """Remove the service user."""
    User.objects.get(username=USERNAME, email=EMAIL).delete()

class Migration(migrations.Migration):

    operations = [
        migrations.RunPython(forwards, backwards),
    ]

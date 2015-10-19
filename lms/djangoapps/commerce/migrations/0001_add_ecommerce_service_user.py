# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from south.db import db
from south.utils import datetime_utils as datetime
from south.v2 import DataMigration


class Migration(DataMigration):
    username = settings.ECOMMERCE_SERVICE_WORKER_USERNAME
    email = username + '@fake.email'

    def forwards(self, orm):
        """Add the service user."""
        user = User.objects.create(username=self.username, email=self.email)
        user.set_unusable_password()
        user.save()

    def backwards(self, orm):
        """Remove the service user."""
        User.objects.get(username=self.username, email=self.email).delete()

    models = {}
    complete_apps = ['commerce']
    symmetrical = True

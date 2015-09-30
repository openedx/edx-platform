# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

from django.conf import settings
from django.contrib.auth.models import User

class Migration(DataMigration):

    def forwards(self, orm):
        """Add the service user."""
        user = User.objects.create(username=settings.ECOMMERCE_SERVICE_WORKER_USERNAME)
        user.set_unusable_password()
        user.save()

    def backwards(self, orm):
        """Remove the service user."""
        User.objects.get(username=settings.ECOMMERCE_SERVICE_WORKER_USERNAME).delete()

    models = {
        
    }

    complete_apps = ['commerce']
    symmetrical = True

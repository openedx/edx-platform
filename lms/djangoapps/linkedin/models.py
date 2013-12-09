from django.contrib.auth.models import User
from django.db import models


class LinkedIn(models.Model):
    user = models.OneToOneField(User, primary_key=True)
    has_linkedin_account = models.NullBooleanField(default=None)

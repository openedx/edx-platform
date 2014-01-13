"""
Models for LinkedIn integration app.
"""
from django.contrib.auth.models import User
from django.db import models


class LinkedIn(models.Model):
    """
    Defines a table for storing a users's LinkedIn status.
    """
    user = models.OneToOneField(User, primary_key=True)
    has_linkedin_account = models.NullBooleanField(default=None)
    emailed_courses = models.TextField(default="[]")  # JSON list of course ids

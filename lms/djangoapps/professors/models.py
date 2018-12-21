import json

from django.contrib.auth.models import User
from django.db import models


class Professor(models.Model):
    """
    professor
    """
    user = models.ForeignKey(User, db_index=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=64, db_index=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    avatar = models.CharField(max_length=255, null=True, blank=True)
    slogan = models.TextField(max_length=1000, null=True, blank=True)
    introduction = models.TextField(max_length=3000, null=True, blank=True)
    main_achievements = models.TextField(max_length=3000, null=True, blank=True)
    education_experience = models.TextField(max_length=3000, null=True, blank=True)
    other_achievements = models.TextField(max_length=3000, null=True, blank=True)
    research_fields = models.TextField(max_length=3000, null=True, blank=True)
    research_papers = models.TextField(max_length=3000, null=True, blank=True)
    project_experience = models.TextField(max_length=3000, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    sort_num = models.IntegerField(default=0)

    class Meta:
        app_label = 'professors'

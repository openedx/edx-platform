"""
Models for course roles schema
"""
from django.db import models


class CourseRolesService(models.Model):
    """
    Model for a course roles service.
    """
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

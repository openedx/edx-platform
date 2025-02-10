"""
Offline mode models.
"""
from django.db import models
from opaque_keys.edx.django.models import CourseKeyField


class OfflineCourseSize(models.Model):
    """
    Model to store the course total offline content size.
    """

    course_id = CourseKeyField(max_length=255, db_index=True, unique=True)
    size = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Offline Course Size"
        verbose_name_plural = "Offline Course Sizes"

    def __str__(self):
        return f"{self.course_id} - {self.size} bytes"

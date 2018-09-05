from django.db import models

from openedx.core.djangoapps.xmodule_django.models import CourseKeyField


class CustomSettings(models.Model):
    """
    Extra Custom Settings for each course
    """
    id = CourseKeyField(max_length=255, db_index=True, primary_key=True)
    is_featured = models.BooleanField(default=False)
    show_grades = models.BooleanField(default=True)
    tags = models.CharField(max_length=255, null=True, blank=True)

    def __unicode__(self):
        return '{} | {}'.format(self.id, self.is_featured)

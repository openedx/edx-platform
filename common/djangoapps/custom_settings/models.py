from django.db import models
from django.db.models.fields import BooleanField

from openedx.core.djangoapps.xmodule_django.models import CourseKeyField


class CustomSettings(models.Model):
    id = CourseKeyField(max_length=255, db_index=True, primary_key=True)
    is_featured = BooleanField(default=False)

    def __unicode__(self):
        return '{} | {}'.format(self.id, self.is_featured)

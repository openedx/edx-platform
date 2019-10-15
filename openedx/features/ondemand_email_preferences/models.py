from django.contrib.auth.models import User
from django.db import models
from openedx.core.djangoapps.xmodule_django.models import CourseKeyField


class OnDemandEmailPreferences(models.Model):
    user = models.ForeignKey(User, db_index=True, related_name='on_demand_email_preferences_user', on_delete=models.CASCADE)
    course_id = CourseKeyField(db_index=True, max_length=255, null=False)
    is_enabled = models.BooleanField(default=True, null=False)

    class Meta(object):
        """ Meta class to make user and course unique together """
        unique_together = ('course_id', 'user')

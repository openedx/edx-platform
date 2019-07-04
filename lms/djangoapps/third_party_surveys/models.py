from django.db import models
from django.contrib.auth.models import User
from model_utils.models import TimeStampedModel


class ThirdPartySurvey(TimeStampedModel):
    """
    Model that stores third party surveys
    """
    response = models.TextField()
    gizmo_survey_id = models.IntegerField()
    request_date = models.DateTimeField()
    user = models.ForeignKey(User, related_name='survey_user')
    survey_type = models.CharField(max_length=20, null=True, blank=True)

    def __unicode__(self):
        return "{} | {} | {}".format(self.gizmo_survey_id, self.user, self.request_date)

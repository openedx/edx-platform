"""
Models for Survey
"""
import json
import logging

from django.db import models
from django.contrib.auth.models import User


log = logging.getLogger(__name__)


class SurveySubmission(models.Model):
    """
    Submissions from survey form.
    """
    course_id = models.CharField(max_length=128, db_index=True)
    unit_id = models.CharField(max_length=255, db_index=True)
    user = models.ForeignKey(User, related_name='survey')
    survey_name = models.CharField(max_length=255, db_index=True)
    survey_answer = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    def get_survey_answer(self):
        js_str = self.survey_answer
        if not js_str:
            js_str = dict()
        else:
            js_str = json.loads(self.survey_answer)

        return js_str

    def set_survey_answer(self, js):
        self.survey_answer = json.dumps(js)

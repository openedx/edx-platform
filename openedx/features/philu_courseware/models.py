from django.db import models
from model_utils.models import TimeStampedModel
from django.contrib.auth.models import User

from opaque_keys.edx.django.models import UsageKeyField

from .constants import COMPETENCY_ASSESSMENT_TYPE_CHOICES, CORRECTNESS_CHOICES


class CompetencyAssessmentRecord(TimeStampedModel):
    chapter_id = models.TextField(max_length=255)
    problem_id = UsageKeyField(max_length=255)
    problem_text = models.TextField(null=False)
    assessment_type = models.CharField(max_length=4, choices=COMPETENCY_ASSESSMENT_TYPE_CHOICES)

    attempt = models.IntegerField()
    correctness = models.CharField(max_length=9, choices=CORRECTNESS_CHOICES)
    # comma separated choice ids for example choice_1,choice_2,choice_3
    choice_id = models.CharField(max_length=255)
    choice_text = models.TextField()
    score = models.FloatField()
    user = models.ForeignKey(User, db_index=True, on_delete=models.CASCADE)
    question_number = models.IntegerField(default=None, blank=True, null=True)

    def __unicode__(self):
        return '{problem}, question({question_number}), {username}, {assessment_type}, attempt({attempt})'.format(
            problem=self.problem_id,
            username=self.user.username,
            assessment_type=self.assessment_type,
            attempt=self.attempt,
            question_number=self.question_number
        )

    class Meta:
        verbose_name = "CompetencyAssessmentRecord"

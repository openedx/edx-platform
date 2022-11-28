from django.db import models
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django_extensions.db.models import TimeStampedModel

from opaque_keys.edx.django.models import CourseKeyField, UsageKeyField  # pylint: disable=import-error

from openedx.features.genplus_features.genplus.models import Skill, Class
from openedx.features.genplus_features.genplus_learning.models import Program

USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


class Assessment(TimeStampedModel):
    user = models.ForeignKey(USER_MODEL, on_delete=models.CASCADE)
    course_id = CourseKeyField(max_length=255, db_index=True)
    usage_id = UsageKeyField(max_length=255, db_index=True)
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    gen_class = models.ForeignKey(Class, on_delete=models.SET_NULL, null=True)
    problem_id = models.CharField(max_length=64)
    assessment_time = models.CharField(max_length=64) 
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    class Meta:
        abstract = True

class UserResponse(Assessment):
    student_response = models.TextField(blank=True, null=True, default=None)
    score = models.IntegerField(blank=True, null=True, default=0)
    class Meta:
        verbose_name = 'User Text Responses'

    def __str__(self):
        return "Score:{} by {}".format(self.score, self.user_id)
    
class UserRating(Assessment):
    rating = models.IntegerField(db_index=True, default=1, validators=[MaxValueValidator(5),MinValueValidator(1)])
    class Meta:
        verbose_name = 'User Rating Responses'

    def __str__(self):
        return "Rating:{} by {}".format(self.rating, self.user_id)

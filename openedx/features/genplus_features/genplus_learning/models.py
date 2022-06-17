from django.db import models
from django_extensions.db.models import TimeStampedModel


class Skill(TimeStampedModel):
    name = models.CharField(max_length=128, unique=True)

    def __str__(self):
        return self.name


class YearGroup(TimeStampedModel):
    name = models.CharField(max_length=128, unique=True)
    year_of_programme = models.CharField(max_length=128)

    def __str__(self):
        return self.name

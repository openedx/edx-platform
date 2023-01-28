from django.db import models

class FxPrograms(models.Model):
    name = models.CharField(max_length=1000, default="")
    program_id = models.CharField(max_length=250, default="")
    courses_list = models.JSONField()
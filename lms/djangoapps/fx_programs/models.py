from django.db import models

class FxPrograms(models.Model):
    program_id = models.CharField(max_length=250, default="")
    name = models.CharField(max_length=1000, default="")
    course_list = models.CharField(max_length=10000, default="")
    id_course_list = models.CharField(max_length=10000, default="")
    metadata = models.JSONField(default="")

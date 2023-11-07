from django.db import models
import os
from datetime import datetime


def attachment_file_name(instance, filename):
    qualified_filename = instance.email + "_" + datetime.today().strftime('%Y%m%d%H%M%S') + "_" + filename
    return qualified_filename

class Feedback(models.Model):
    email = models.EmailField(max_length=250, default="")
    category_id = models.CharField(max_length=250, default="")
    content = models.CharField(max_length=5000)
    attachment = models.ImageField(upload_to=attachment_file_name)
    course_id = models.CharField(max_length=255)
    lesson_url = models.URLField(max_length=5000, default="")
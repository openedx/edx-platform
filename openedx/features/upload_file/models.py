from django.db import models
from datetime import datetime

def attachment_file_name(instance, filename):
    qualified_filename = instance.email + "_" + datetime.today().strftime('%Y%m%d%H%M%S') + "_" + filename
    return qualified_filename

class UploadFile(models.Model):
    email = models.EmailField(max_length=250)
    block_id = models.CharField(max_length=255)
    course_id = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    file = models.ImageField(upload_to=attachment_file_name)
    date =  models.DateTimeField(auto_now_add=True)
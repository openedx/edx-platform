from django.contrib.auth.models import User
from django.db import models


class Requirement(models.Model):
    """Essentially a requirements.txt for each course
    
    Keeping it here prevents file conflicts if there are concurrent writes
    """
    course = models.CharField(max_length=255)
    package_name = models.CharField(max_length=100)
    version = models.CharField(max_length=15, null=True)

    def __unicode__(self):
        return "{}=={}".format(self.package_name, self.version)


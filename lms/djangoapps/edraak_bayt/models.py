from django.db import models


class BaytPublishedCertificate(models.Model):
    user_id = models.IntegerField(blank=True, null=True, db_index=True)
    course_id = models.CharField(blank=True, null=True, db_index=True, max_length=255)
from django.db import models

# Create your models here.
class AnonymousUserExpt(models.Model):
    username = models.CharField(max_length=64, db_index=True, null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    created_datetime = models.DateTimeField(auto_now_add=True, null=True)
    modified_datetime = models.DateTimeField(auto_now=True, null=True)

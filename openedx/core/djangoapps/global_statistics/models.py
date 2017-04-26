from django.db import models


class TokenStorage(models.Model):
    secret_token = models.CharField(max_length=255, null=True)

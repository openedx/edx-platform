from django.db import models


class GenericModel(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    created = models.DateField()

    class Meta:
        ordering = ('name',)

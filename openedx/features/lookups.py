from django.db import models

models.CharField.register_lookup(models.functions.Length, 'length')

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('appsembler_lms', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='users',
            field=models.ManyToManyField(help_text='List of users in an organization', to=settings.AUTH_USER_MODEL, blank=True),
        ),
    ]

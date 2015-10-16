# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='registration',
            name='user',
            field=models.OneToOneField(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='userstanding',
            name='user',
            field=models.OneToOneField(related_name='standing', to=settings.AUTH_USER_MODEL),
        ),
    ]

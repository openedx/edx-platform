# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.OAUTH2_PROVIDER_APPLICATION_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='RestrictedApplication',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('application', models.ForeignKey(to=settings.OAUTH2_PROVIDER_APPLICATION_MODEL)),
            ],
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserLeads',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('utm_source', models.CharField(default=None, max_length=255)),
                ('utm_medium', models.CharField(default=None, max_length=255)),
                ('utm_campaign', models.CharField(default=None, max_length=255)),
                ('utm_content', models.CharField(default=None, max_length=255)),
                ('utm_term', models.CharField(default=None, max_length=255)),
                ('date_created', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]

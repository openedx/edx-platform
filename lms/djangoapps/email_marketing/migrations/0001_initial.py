# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailMarketingConfiguration',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('change_date', models.DateTimeField(auto_now_add=True, verbose_name='Change date')),
                ('enabled', models.BooleanField(default=False, verbose_name='Enabled')),
                ('sailthru_enabled', models.BooleanField(default=False, help_text='Enable Sailthru integration.')),
                ('sailthru_key', models.CharField(help_text='Sailthru api key.', max_length=32, null=True, blank=True)),
                ('sailthru_secret', models.CharField(help_text='Sailthru secret.', max_length=32, null=True, blank=True)),
                ('sailthru_new_user_list', models.CharField(help_text='Sailthru new user list.', max_length=32, null=True, blank=True)),
                ('sailthru_retry_interval', models.IntegerField(default=3600, help_text='Sailthru connection retry interval (secs).')),
                ('sailthru_max_retries', models.IntegerField(default=24, help_text='Sailthru maximum retries.')),
                ('changed_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='Changed by')),
            ],
        ),
    ]
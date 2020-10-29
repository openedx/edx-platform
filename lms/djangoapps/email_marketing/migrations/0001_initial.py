# -*- coding: utf-8 -*-


import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


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
                ('sailthru_key', models.CharField(help_text='API key for accessing Sailthru. ', max_length=32)),
                ('sailthru_secret', models.CharField(help_text='API secret for accessing Sailthru. ', max_length=32)),
                ('sailthru_new_user_list', models.CharField(help_text='Sailthru list name to add new users to. ', max_length=48)),
                ('sailthru_retry_interval', models.IntegerField(default=3600, help_text='Sailthru connection retry interval (secs).')),
                ('sailthru_max_retries', models.IntegerField(default=24, help_text='Sailthru maximum retries.')),
                ('sailthru_activation_template', models.CharField(help_text='Sailthru template to use on activation send. ', max_length=20)),
                ('changed_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='Changed by')),
            ],
        ),
    ]

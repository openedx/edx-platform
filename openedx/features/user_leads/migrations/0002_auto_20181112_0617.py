# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_leads', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='userleads',
            options={'verbose_name': 'User Lead', 'verbose_name_plural': 'User Leads'},
        ),
        migrations.AlterField(
            model_name='userleads',
            name='utm_campaign',
            field=models.CharField(default=None, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='userleads',
            name='utm_content',
            field=models.CharField(default=None, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='userleads',
            name='utm_medium',
            field=models.CharField(default=None, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='userleads',
            name='utm_source',
            field=models.CharField(default=None, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='userleads',
            name='utm_term',
            field=models.CharField(default=None, max_length=255, null=True),
        ),
    ]

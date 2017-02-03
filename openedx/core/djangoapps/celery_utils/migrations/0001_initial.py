# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
import jsonfield.fields
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='FailedTask',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('task_name', models.CharField(max_length=255)),
                ('task_id', models.CharField(max_length=255, db_index=True)),
                ('args', jsonfield.fields.JSONField(blank=True)),
                ('kwargs', jsonfield.fields.JSONField(blank=True)),
                ('exc', models.CharField(max_length=255)),
                ('datetime_resolved', models.DateTimeField(default=None, null=True, db_index=True, blank=True)),
            ],
        ),
        migrations.AlterIndexTogether(
            name='failedtask',
            index_together=set([('task_name', 'exc')]),
        ),
    ]

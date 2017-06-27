# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('experiments', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExperimentKeyValue',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('experiment_id', models.PositiveSmallIntegerField(verbose_name=b'Experiment ID', db_index=True)),
                ('key', models.CharField(max_length=255)),
                ('value', models.TextField()),
            ],
            options={
                'verbose_name': 'Experiment Data',
                'verbose_name_plural': 'Experiment Data',
            },
        ),
        migrations.AlterUniqueTogether(
            name='experimentkeyvalue',
            unique_together=set([('experiment_id', 'key')]),
        ),
    ]

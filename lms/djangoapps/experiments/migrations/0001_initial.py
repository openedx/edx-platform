# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ExperimentData',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('experiment_id', models.PositiveSmallIntegerField(verbose_name=b'Experiment ID', db_index=True)),
                ('key', models.CharField(max_length=255)),
                ('value', models.TextField()),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Experiment Data',
                'verbose_name_plural': 'Experiment Data',
            },
        ),
        migrations.AlterUniqueTogether(
            name='experimentdata',
            unique_together=set([('user', 'experiment_id', 'key')]),
        ),
        migrations.AlterIndexTogether(
            name='experimentdata',
            index_together=set([('user', 'experiment_id')]),
        ),
    ]

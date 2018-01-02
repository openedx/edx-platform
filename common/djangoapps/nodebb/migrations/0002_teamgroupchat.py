# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('teams', '0001_initial'),
        ('nodebb', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TeamGroupChat',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('room_id', models.IntegerField(unique=True)),
                ('team', models.ForeignKey(related_name='team', to='teams.CourseTeam')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]

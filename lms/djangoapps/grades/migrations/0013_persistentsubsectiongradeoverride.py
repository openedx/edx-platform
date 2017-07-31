# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

from coursewarehistoryextended.fields import UnsignedBigIntOneToOneField


class Migration(migrations.Migration):

    dependencies = [
        ('grades', '0012_computegradessetting'),
    ]

    operations = [
        migrations.CreateModel(
            name='PersistentSubsectionGradeOverride',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, db_index=True)),
                ('earned_all_override', models.FloatField(null=True, blank=True)),
                ('possible_all_override', models.FloatField(null=True, blank=True)),
                ('earned_graded_override', models.FloatField(null=True, blank=True)),
                ('possible_graded_override', models.FloatField(null=True, blank=True)),
                ('grade', UnsignedBigIntOneToOneField(related_name='override', to='grades.PersistentSubsectionGrade')),
            ],
        ),
    ]

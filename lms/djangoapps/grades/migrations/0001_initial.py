# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import coursewarehistoryextended.fields
import django.utils.timezone
import model_utils.fields
from openedx.core.djangoapps.xmodule_django.models import CourseKeyField, UsageKeyField


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='PersistentSubsectionGrade',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('id', coursewarehistoryextended.fields.UnsignedBigIntAutoField(serialize=False, primary_key=True)),
                ('user_id', models.IntegerField()),
                ('course_id', CourseKeyField(max_length=255)),
                ('usage_key', UsageKeyField(max_length=255)),
                ('subtree_edited_date', models.DateTimeField(verbose_name=b'last content edit timestamp')),
                ('course_version', models.CharField(max_length=255, verbose_name=b'guid of latest course version', blank=True)),
                ('earned_all', models.FloatField()),
                ('possible_all', models.FloatField()),
                ('earned_graded', models.FloatField()),
                ('possible_graded', models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name='VisibleBlocks',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('blocks_json', models.TextField()),
                ('hashed', models.CharField(unique=True, max_length=100)),
            ],
        ),
        migrations.AddField(
            model_name='persistentsubsectiongrade',
            name='visible_blocks',
            field=models.ForeignKey(to='grades.VisibleBlocks', db_column=b'visible_blocks_hash', to_field=b'hashed'),
        ),
        migrations.AlterUniqueTogether(
            name='persistentsubsectiongrade',
            unique_together=set([('course_id', 'user_id', 'usage_key')]),
        ),
    ]

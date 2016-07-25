# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import coursewarehistoryextended.fields
import django.utils.timezone
import model_utils.fields
import xmodule_django.models


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
                ('subtree_edited_date', models.DateTimeField(verbose_name=b'last content edit timestamp')),
                ('user_id', models.CharField(max_length=255)),
                ('earned_all', models.IntegerField()),
                ('possible_all', models.IntegerField()),
                ('earned_graded', models.IntegerField()),
                ('possible_graded', models.IntegerField()),
                ('course_id', xmodule_django.models.CourseKeyField(max_length=255)),
                ('usage_key', xmodule_django.models.UsageKeyField(max_length=255)),
                ('course_version', models.CharField(max_length=255, verbose_name=b'guid of latest course version')),
            ],
        ),
        migrations.CreateModel(
            name='VisibleBlocks',
            fields=[
                ('_blocks_json', models.TextField(db_column=b'blocks_json')),
                ('hashed', models.CharField(max_length=32, serialize=False, primary_key=True)),
            ],
        ),
        migrations.AddField(
            model_name='persistentsubsectiongrade',
            name='visible_blocks',
            field=models.ForeignKey(to='grades.VisibleBlocks'),
        ),
        migrations.AlterUniqueTogether(
            name='persistentsubsectiongrade',
            unique_together=set([('user_id', 'usage_key')]),
        ),
        migrations.AlterIndexTogether(
            name='persistentsubsectiongrade',
            index_together=set([('user_id', 'usage_key')]),
        ),
    ]

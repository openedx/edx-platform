# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('oef', '0005_topicquestion_order_number'),
    ]

    operations = [
        migrations.CreateModel(
            name='Instruction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('question_index', models.IntegerField()),
                ('question', models.TextField()),
                ('answer', models.TextField()),
                ('is_enabled', models.BooleanField(default=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='oefsurvey',
            name='description',
            field=models.TextField(default='Description'),
            preserve_default=False,
        ),
    ]

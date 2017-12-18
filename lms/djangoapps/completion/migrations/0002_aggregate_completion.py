# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import lms.djangoapps.completion.models
import django.utils.timezone
from django.conf import settings
import model_utils.fields
import openedx.core.djangoapps.xmodule_django.models
import openedx.core.djangolib.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('completion', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AggregateCompletion',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('id', openedx.core.djangolib.fields.BigAutoField(serialize=False, primary_key=True)),
                ('course_key', openedx.core.djangoapps.xmodule_django.models.CourseKeyField(max_length=255)),
                ('aggregation_name', models.CharField(max_length=255)),
                ('block_key', openedx.core.djangoapps.xmodule_django.models.UsageKeyField(max_length=255)),
                ('earned', models.FloatField(validators=[lms.djangoapps.completion.models.validate_positive_float])),
                ('possible', models.FloatField(validators=[lms.djangoapps.completion.models.validate_positive_float])),
                ('percent', models.FloatField(validators=[lms.djangoapps.completion.models.validate_percent])),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='aggregatecompletion',
            unique_together=set([('course_key', 'block_key', 'user', 'aggregation_name')]),
        ),
        migrations.AlterIndexTogether(
            name='aggregatecompletion',
            index_together=set([('course_key', 'aggregation_name', 'block_key', 'percent'), ('user', 'aggregation_name', 'course_key', 'block_key')]),
        ),
    ]

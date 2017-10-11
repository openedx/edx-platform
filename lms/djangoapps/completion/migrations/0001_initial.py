# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
from django.conf import settings
import model_utils.fields

import lms.djangoapps.completion.models
import openedx.core.djangoapps.xmodule_django.models

# pylint: disable=ungrouped-imports
try:
    from django.models import BigAutoField  # New in django 1.10
except ImportError:
    from openedx.core.djangolib.fields import BigAutoField
# pylint: enable=ungrouped-imports

class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BlockCompletion',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('id', BigAutoField(serialize=False, primary_key=True)),
                ('course_key', openedx.core.djangoapps.xmodule_django.models.CourseKeyField(max_length=255)),
                ('block_key', openedx.core.djangoapps.xmodule_django.models.UsageKeyField(max_length=255)),
                ('block_type', models.CharField(max_length=64)),
                ('completion', models.FloatField(validators=[lms.djangoapps.completion.models.validate_percent])),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='blockcompletion',
            unique_together=set([('course_key', 'block_key', 'user')]),
        ),
        migrations.AlterIndexTogether(
            name='blockcompletion',
            index_together=set([('course_key', 'block_type', 'user'), ('user', 'course_key', 'modified')]),
        ),
    ]

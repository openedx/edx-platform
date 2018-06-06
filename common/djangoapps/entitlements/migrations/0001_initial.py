# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
from django.conf import settings
import model_utils.fields
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0013_delete_historical_enrollment_records'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseEntitlement',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('course_uuid', models.UUIDField()),
                ('expired_at', models.DateTimeField(null=True)),
                ('mode', models.CharField(default=b'audit', max_length=100)),
                ('order_number', models.CharField(max_length=128, null=True)),
                ('enrollment_course_run', models.ForeignKey(to='student.CourseEnrollment', null=True, on_delete=models.CASCADE)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]

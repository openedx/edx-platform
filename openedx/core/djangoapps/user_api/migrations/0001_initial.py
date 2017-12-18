# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
from django.conf import settings
import model_utils.fields
import django.core.validators
from openedx.core.djangoapps.xmodule_django.models import CourseKeyField


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserCourseTag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('key', models.CharField(max_length=255, db_index=True)),
                ('course_id', CourseKeyField(max_length=255, db_index=True)),
                ('value', models.TextField()),
                ('user', models.ForeignKey(related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='UserOrgTag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('key', models.CharField(max_length=255, db_index=True)),
                ('org', models.CharField(max_length=255, db_index=True)),
                ('value', models.TextField()),
                ('user', models.ForeignKey(related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='UserPreference',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('key', models.CharField(db_index=True, max_length=255, validators=[django.core.validators.RegexValidator(b'[-_a-zA-Z0-9]+')])),
                ('value', models.TextField()),
                ('user', models.ForeignKey(related_name='preferences', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='userpreference',
            unique_together=set([('user', 'key')]),
        ),
        migrations.AlterUniqueTogether(
            name='userorgtag',
            unique_together=set([('user', 'org', 'key')]),
        ),
        migrations.AlterUniqueTogether(
            name='usercoursetag',
            unique_together=set([('user', 'course_id', 'key')]),
        ),
    ]

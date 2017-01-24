# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields
import badges.models
from django.conf import settings
import django.utils.timezone
from model_utils import fields
from openedx.core.djangoapps.xmodule_django.models import CourseKeyField


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BadgeAssertion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('data', jsonfield.fields.JSONField()),
                ('backend', models.CharField(max_length=50)),
                ('image_url', models.URLField()),
                ('assertion_url', models.URLField()),
                ('modified', fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('created', fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False, db_index=True)),
            ],
        ),
        migrations.CreateModel(
            name='BadgeClass',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('slug', models.SlugField(max_length=255, validators=[badges.models.validate_lowercase])),
                ('issuing_component', models.SlugField(default=b'', blank=True, validators=[badges.models.validate_lowercase])),
                ('display_name', models.CharField(max_length=255)),
                ('course_id', CourseKeyField(default=None, max_length=255, blank=True)),
                ('description', models.TextField()),
                ('criteria', models.TextField()),
                ('mode', models.CharField(default=b'', max_length=100, blank=True)),
                ('image', models.ImageField(upload_to=b'badge_classes', validators=[badges.models.validate_badge_image])),
            ],
        ),
        migrations.CreateModel(
            name='CourseCompleteImageConfiguration',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('mode', models.CharField(help_text='The course mode for this badge image. For example, "verified" or "honor".', unique=True, max_length=125)),
                ('icon', models.ImageField(help_text='Badge images must be square PNG files. The file size should be under 250KB.', upload_to=b'course_complete_badges', validators=[badges.models.validate_badge_image])),
                ('default', models.BooleanField(default=False, help_text='Set this value to True if you want this image to be the default image for any course modes that do not have a specified badge image. You can have only one default image.')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='badgeclass',
            unique_together=set([('slug', 'issuing_component', 'course_id')]),
        ),
        migrations.AddField(
            model_name='badgeassertion',
            name='badge_class',
            field=models.ForeignKey(to='badges.BadgeClass'),
        ),
        migrations.AddField(
            model_name='badgeassertion',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
    ]

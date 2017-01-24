# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from openedx.core.djangoapps.xmodule_django.models import CourseKeyField


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CourseMode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('course_id', CourseKeyField(max_length=255, verbose_name='Course', db_index=True)),
                ('mode_slug', models.CharField(max_length=100, verbose_name='Mode')),
                ('mode_display_name', models.CharField(max_length=255, verbose_name='Display Name')),
                ('min_price', models.IntegerField(default=0, verbose_name='Price')),
                ('currency', models.CharField(default=b'usd', max_length=8)),
                ('expiration_datetime', models.DateTimeField(default=None, help_text='OPTIONAL: After this date/time, users will no longer be able to enroll in this mode. Leave this blank if users can enroll in this mode until enrollment closes for the course.', null=True, verbose_name='Upgrade Deadline', blank=True)),
                ('expiration_date', models.DateField(default=None, null=True, blank=True)),
                ('suggested_prices', models.CommaSeparatedIntegerField(default=b'', max_length=255, blank=True)),
                ('description', models.TextField(null=True, blank=True)),
                ('sku', models.CharField(help_text='OPTIONAL: This is the SKU (stock keeping unit) of this mode in the external ecommerce service.  Leave this blank if the course has not yet been migrated to the ecommerce service.', max_length=255, null=True, verbose_name=b'SKU', blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='CourseModesArchive',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('course_id', CourseKeyField(max_length=255, db_index=True)),
                ('mode_slug', models.CharField(max_length=100)),
                ('mode_display_name', models.CharField(max_length=255)),
                ('min_price', models.IntegerField(default=0)),
                ('suggested_prices', models.CommaSeparatedIntegerField(default=b'', max_length=255, blank=True)),
                ('currency', models.CharField(default=b'usd', max_length=8)),
                ('expiration_date', models.DateField(default=None, null=True, blank=True)),
                ('expiration_datetime', models.DateTimeField(default=None, null=True, blank=True)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='coursemode',
            unique_together=set([('course_id', 'mode_slug', 'currency')]),
        ),
    ]

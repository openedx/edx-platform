# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings
import django_countries.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('student', '0008_auto_20161117_1209'),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoricalUserProfile',
            fields=[
                ('id', models.IntegerField(verbose_name='ID', db_index=True, auto_created=True, blank=True)),
                ('name', models.CharField(db_index=True, max_length=255, blank=True)),
                ('meta', models.TextField(blank=True)),
                ('courseware', models.CharField(default=b'course.xml', max_length=255, blank=True)),
                ('language', models.CharField(db_index=True, max_length=255, blank=True)),
                ('location', models.CharField(db_index=True, max_length=255, blank=True)),
                ('year_of_birth', models.IntegerField(db_index=True, null=True, blank=True)),
                ('gender', models.CharField(blank=True, max_length=6, null=True, db_index=True, choices=[(b'm', b'Male'), (b'f', b'Female'), (b'o', b'Other/Prefer Not to Say')])),
                ('level_of_education', models.CharField(blank=True, max_length=6, null=True, db_index=True, choices=[(b'p', b'Doctorate'), (b'm', b"Master's or professional degree"), (b'b', b"Bachelor's degree"), (b'a', b'Associate degree'), (b'hs', b'Secondary/high school'), (b'jhs', b'Junior secondary/junior high/middle school'), (b'el', b'Elementary/primary school'), (b'none', b'No formal education'), (b'other', b'Other education')])),
                ('mailing_address', models.TextField(null=True, blank=True)),
                ('city', models.TextField(null=True, blank=True)),
                ('country', django_countries.fields.CountryField(blank=True, max_length=2, null=True)),
                ('goals', models.TextField(null=True, blank=True)),
                ('allow_certificate', models.BooleanField(default=1)),
                ('bio', models.CharField(max_length=3000, null=True, blank=True)),
                ('profile_image_uploaded_at', models.DateTimeField(null=True, blank=True)),
                ('history_id', models.AutoField(serialize=False, primary_key=True)),
                ('history_date', models.DateTimeField()),
                ('start_date', models.DateTimeField(null=True, blank=True)),
                ('end_date', models.DateTimeField(null=True, blank=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(max_length=1, choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')])),
                ('history_user', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, null=True)),
                ('user', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.DO_NOTHING, db_constraint=False, blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
                'verbose_name': 'historical user profile',
            },
        ),
    ]

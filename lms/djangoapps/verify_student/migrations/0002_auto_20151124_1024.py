# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import model_utils.fields
import xmodule_django.models
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('verify_student', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='VerificationDeadline',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('course_key', xmodule_django.models.CourseKeyField(help_text='The course for which this deadline applies', unique=True, max_length=255, db_index=True)),
                ('deadline', models.DateTimeField(help_text='The datetime after which users are no longer allowed to submit photos for verification.')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='HistoricalVerificationDeadline',
            fields=[
                ('id', models.IntegerField(verbose_name='ID', db_index=True, auto_created=True, blank=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('course_key', xmodule_django.models.CourseKeyField(help_text='The course for which this deadline applies', max_length=255, db_index=True)),
                ('deadline', models.DateTimeField(help_text='The datetime after which users are no longer allowed to submit photos for verification.')),
                ('history_id', models.AutoField(serialize=False, primary_key=True)),
                ('history_date', models.DateTimeField()),
                ('history_type', models.CharField(max_length=1, choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')])),
                ('history_user', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
                'verbose_name': 'historical verification deadline',
            },
        ),
        migrations.CreateModel(
            name='IcrvStatusEmailsConfiguration',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('change_date', models.DateTimeField(auto_now_add=True, verbose_name='Change date')),
                ('enabled', models.BooleanField(default=False, verbose_name='Enabled')),
                ('changed_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='Changed by')),
            ],
            options={
                'ordering': ('-change_date',),
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='softwaresecurephotoverification',
            name='copy_id_photo_from',
            field=models.ForeignKey(blank=True, to='verify_student.SoftwareSecurePhotoVerification', null=True),
        ),
        migrations.AddField(
            model_name='historicalverificationdeadline',
            name='deadline_is_explicit',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='verificationdeadline',
            name='deadline_is_explicit',
            field=models.BooleanField(default=True),
        ),
    ]

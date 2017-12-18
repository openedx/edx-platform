# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import lms.djangoapps.verify_student.models
import model_utils.fields
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from openedx.core.djangoapps.xmodule_django.models import CourseKeyField


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoricalVerificationDeadline',
            fields=[
                ('id', models.IntegerField(verbose_name='ID', db_index=True, auto_created=True, blank=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('course_key', CourseKeyField(help_text='The course for which this deadline applies', max_length=255, db_index=True)),
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
        migrations.CreateModel(
            name='InCourseReverificationConfiguration',
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
        migrations.CreateModel(
            name='SkippedReverification',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('course_id', CourseKeyField(max_length=255, db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='SoftwareSecurePhotoVerification',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('status', model_utils.fields.StatusField(default=b'created', max_length=100, verbose_name='status', no_check_for_status=True, choices=[(b'created', b'created'), (b'ready', b'ready'), (b'submitted', b'submitted'), (b'must_retry', b'must_retry'), (b'approved', b'approved'), (b'denied', b'denied')])),
                ('status_changed', model_utils.fields.MonitorField(default=django.utils.timezone.now, verbose_name='status changed', monitor='status')),
                ('name', models.CharField(max_length=255, blank=True)),
                ('face_image_url', models.URLField(max_length=255, blank=True)),
                ('photo_id_image_url', models.URLField(max_length=255, blank=True)),
                ('receipt_id', models.CharField(default=lms.djangoapps.verify_student.models.generateUUID, max_length=255, db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True, db_index=True)),
                ('display', models.BooleanField(default=True, db_index=True)),
                ('submitted_at', models.DateTimeField(null=True, db_index=True)),
                ('reviewing_service', models.CharField(max_length=255, blank=True)),
                ('error_msg', models.TextField(blank=True)),
                ('error_code', models.CharField(max_length=50, blank=True)),
                ('photo_id_key', models.TextField(max_length=1024)),
                ('copy_id_photo_from', models.ForeignKey(blank=True, to='verify_student.SoftwareSecurePhotoVerification', null=True)),
                ('reviewing_user', models.ForeignKey(related_name='photo_verifications_reviewed', default=None, to=settings.AUTH_USER_MODEL, null=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='VerificationCheckpoint',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('course_id', CourseKeyField(max_length=255, db_index=True)),
                ('checkpoint_location', models.CharField(max_length=255)),
                ('photo_verification', models.ManyToManyField(to='verify_student.SoftwareSecurePhotoVerification')),
            ],
        ),
        migrations.CreateModel(
            name='VerificationDeadline',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('course_key', CourseKeyField(help_text='The course for which this deadline applies', unique=True, max_length=255, db_index=True)),
                ('deadline', models.DateTimeField(help_text='The datetime after which users are no longer allowed to submit photos for verification.')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='VerificationStatus',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('status', models.CharField(db_index=True, max_length=32, choices=[(b'submitted', b'submitted'), (b'approved', b'approved'), (b'denied', b'denied'), (b'error', b'error')])),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('response', models.TextField(null=True, blank=True)),
                ('error', models.TextField(null=True, blank=True)),
                ('checkpoint', models.ForeignKey(related_name='checkpoint_status', to='verify_student.VerificationCheckpoint')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'get_latest_by': 'timestamp',
                'verbose_name': 'Verification Status',
                'verbose_name_plural': 'Verification Statuses',
            },
        ),
        migrations.AddField(
            model_name='skippedreverification',
            name='checkpoint',
            field=models.ForeignKey(related_name='skipped_checkpoint', to='verify_student.VerificationCheckpoint'),
        ),
        migrations.AddField(
            model_name='skippedreverification',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='verificationcheckpoint',
            unique_together=set([('course_id', 'checkpoint_location')]),
        ),
        migrations.AlterUniqueTogether(
            name='skippedreverification',
            unique_together=set([('user', 'course_id')]),
        ),
    ]

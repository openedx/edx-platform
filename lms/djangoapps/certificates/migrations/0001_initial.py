# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import certificates.models
import model_utils.fields
import django_extensions.db.fields
import django_extensions.db.fields.json
import django.db.models.deletion
import django.utils.timezone
from badges.models import validate_badge_image
from django.conf import settings
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
                ('course_id', CourseKeyField(default=None, max_length=255, blank=True)),
                ('mode', models.CharField(max_length=100)),
                ('data', django_extensions.db.fields.json.JSONField()),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='BadgeImageConfiguration',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('mode', models.CharField(help_text='The course mode for this badge image. For example, "verified" or "honor".', unique=True, max_length=125)),
                ('icon', models.ImageField(help_text='Badge images must be square PNG files. The file size should be under 250KB.', upload_to=b'badges', validators=[validate_badge_image])),
                ('default', models.BooleanField(default=False, help_text='Set this value to True if you want this image to be the default image for any course modes that do not have a specified badge image. You can have only one default image.')),
            ],
        ),
        migrations.CreateModel(
            name='CertificateGenerationConfiguration',
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
            name='CertificateGenerationCourseSetting',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('course_key', CourseKeyField(max_length=255, db_index=True)),
                ('enabled', models.BooleanField(default=False)),
            ],
            options={
                'get_latest_by': 'created',
            },
        ),
        migrations.CreateModel(
            name='CertificateHtmlViewConfiguration',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('change_date', models.DateTimeField(auto_now_add=True, verbose_name='Change date')),
                ('enabled', models.BooleanField(default=False, verbose_name='Enabled')),
                ('configuration', models.TextField(help_text=b'Certificate HTML View Parameters (JSON)')),
                ('changed_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='Changed by')),
            ],
            options={
                'ordering': ('-change_date',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CertificateTemplate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('name', models.CharField(help_text='Name of template.', max_length=255)),
                ('description', models.CharField(help_text='Description and/or admin notes.', max_length=255, null=True, blank=True)),
                ('template', models.TextField(help_text='Django template HTML.')),
                ('organization_id', models.IntegerField(help_text='Organization of template.', null=True, db_index=True, blank=True)),
                ('course_key', CourseKeyField(db_index=True, max_length=255, null=True, blank=True)),
                ('mode', models.CharField(default=b'honor', choices=[(b'verified', b'verified'), (b'honor', b'honor'), (b'audit', b'audit'), (b'professional', b'professional'), (b'no-id-professional', b'no-id-professional')], max_length=125, blank=True, help_text='The course mode for this template.', null=True)),
                ('is_active', models.BooleanField(default=False, help_text='On/Off switch.')),
            ],
            options={
                'get_latest_by': 'created',
            },
        ),
        migrations.CreateModel(
            name='CertificateTemplateAsset',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('description', models.CharField(help_text='Description of the asset.', max_length=255, null=True, blank=True)),
                ('asset', models.FileField(help_text='Asset file. It could be an image or css file.', max_length=255, upload_to=certificates.models.template_assets_path)),
            ],
            options={
                'get_latest_by': 'created',
            },
        ),
        migrations.CreateModel(
            name='CertificateWhitelist',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('course_id', CourseKeyField(default=None, max_length=255, blank=True)),
                ('whitelist', models.BooleanField(default=0)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('notes', models.TextField(default=None, null=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ExampleCertificate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('description', models.CharField(help_text="A human-readable description of the example certificate.  For example, 'verified' or 'honor' to differentiate between two types of certificates.", max_length=255)),
                ('uuid', models.CharField(default=certificates.models._make_uuid, help_text='A unique identifier for the example certificate.  This is used when we receive a response from the queue to determine which example certificate was processed.', unique=True, max_length=255, db_index=True)),
                ('access_key', models.CharField(default=certificates.models._make_uuid, help_text='An access key for the example certificate.  This is used when we receive a response from the queue to validate that the sender is the same entity we asked to generate the certificate.', max_length=255, db_index=True)),
                ('full_name', models.CharField(default='John Do\xeb', help_text='The full name that will appear on the certificate.', max_length=255)),
                ('template', models.CharField(help_text='The template file to use when generating the certificate.', max_length=255)),
                ('status', models.CharField(default=b'started', help_text='The status of the example certificate.', max_length=255, choices=[(b'started', b'Started'), (b'success', b'Success'), (b'error', b'Error')])),
                ('error_reason', models.TextField(default=None, help_text='The reason an error occurred during certificate generation.', null=True)),
                ('download_url', models.CharField(default=None, max_length=255, null=True, help_text='The download URL for the generated certificate.')),
            ],
        ),
        migrations.CreateModel(
            name='ExampleCertificateSet',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('course_key', CourseKeyField(max_length=255, db_index=True)),
            ],
            options={
                'get_latest_by': 'created',
            },
        ),
        migrations.CreateModel(
            name='GeneratedCertificate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('course_id', CourseKeyField(default=None, max_length=255, blank=True)),
                ('verify_uuid', models.CharField(default=b'', max_length=32, blank=True)),
                ('download_uuid', models.CharField(default=b'', max_length=32, blank=True)),
                ('download_url', models.CharField(default=b'', max_length=128, blank=True)),
                ('grade', models.CharField(default=b'', max_length=5, blank=True)),
                ('key', models.CharField(default=b'', max_length=32, blank=True)),
                ('distinction', models.BooleanField(default=False)),
                ('status', models.CharField(default=b'unavailable', max_length=32)),
                ('mode', models.CharField(default=b'honor', max_length=32, choices=[(b'verified', b'verified'), (b'honor', b'honor'), (b'audit', b'audit'), (b'professional', b'professional'), (b'no-id-professional', b'no-id-professional')])),
                ('name', models.CharField(max_length=255, blank=True)),
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('modified_date', models.DateTimeField(auto_now=True)),
                ('error_reason', models.CharField(default=b'', max_length=512, blank=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='examplecertificate',
            name='example_cert_set',
            field=models.ForeignKey(to='certificates.ExampleCertificateSet'),
        ),
        migrations.AlterUniqueTogether(
            name='certificatetemplate',
            unique_together=set([('organization_id', 'course_key', 'mode')]),
        ),
        migrations.AlterUniqueTogether(
            name='generatedcertificate',
            unique_together=set([('user', 'course_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='badgeassertion',
            unique_together=set([('course_id', 'user', 'mode')]),
        ),
    ]

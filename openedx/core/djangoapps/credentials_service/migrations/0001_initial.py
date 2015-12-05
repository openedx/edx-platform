# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
import openedx.core.djangoapps.credentials_service.models
import model_utils.fields
import xmodule_django.models


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AbstractCredential',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('credential_type', models.CharField(default=b'courses', max_length=32, choices=[(b'programs', 'programs'), (b'courses', 'courses')])),
                ('is_active', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CertificateTemplate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('name', models.CharField(max_length=255, db_index=True)),
                ('content', models.TextField(help_text='Template content data.')),
                ('certificate_type', models.CharField(blank=True, max_length=32, null=True, choices=[('Honor', b'honor'), ('Verified', b'verified'), ('Professional', b'professional')])),
                ('organization_id', models.IntegerField(help_text='Organization of template.', null=True, db_index=True, blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CertificateTemplateAsset',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('name', models.CharField(max_length=255)),
                ('asset_file', models.FileField(help_text='Asset file. It could be an image or css file.', max_length=255, upload_to=openedx.core.djangoapps.credentials_service.models.assets_path)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Signatory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('name', models.CharField(max_length=255)),
                ('title', models.CharField(max_length=255)),
                ('image', models.ImageField(help_text='Image must be square PNG files. The file size should be under 250KB.', upload_to=openedx.core.djangoapps.credentials_service.models.assets_path, validators=[openedx.core.djangoapps.credentials_service.models.validate_image])),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='UserCredential',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('username', models.CharField(max_length=255, db_index=True)),
                ('status', models.CharField(default=b'awarded', max_length=32, choices=[(b'awarded', 'awarded'), (b'revoked', 'revoked')])),
                ('download_url', models.CharField(help_text='Download URL for the PDFs.', max_length=128, null=True, blank=True)),
                ('uuid', models.CharField(max_length=32)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='AbstractCertificate',
            fields=[
                ('abstractcredential_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='credentials_service.AbstractCredential')),
                ('title', models.CharField(max_length=255, null=True, blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('credentials_service.abstractcredential',),
        ),
        migrations.CreateModel(
            name='UserCredentialAttribute',
            fields=[
                ('usercredential_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='credentials_service.UserCredential')),
                ('namespace', models.CharField(max_length=255)),
                ('name', models.CharField(max_length=255)),
                ('value', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
            bases=('credentials_service.usercredential',),
        ),
        migrations.AddField(
            model_name='usercredential',
            name='credential',
            field=models.ForeignKey(to='credentials_service.AbstractCredential'),
        ),
        migrations.AddField(
            model_name='abstractcredential',
            name='site',
            field=models.ForeignKey(to='sites.Site'),
        ),
        migrations.CreateModel(
            name='CourseCertificate',
            fields=[
                ('abstractcertificate_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='credentials_service.AbstractCertificate')),
                ('course_id', xmodule_django.models.CourseKeyField(max_length=255)),
                ('certificate_type', models.CharField(max_length=32, choices=[('Honor', b'honor'), ('Verified', b'verified'), ('Professional', b'professional')])),
            ],
            bases=('credentials_service.abstractcertificate',),
        ),
        migrations.CreateModel(
            name='ProgramCertificate',
            fields=[
                ('abstractcertificate_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='credentials_service.AbstractCertificate')),
                ('program_id', models.IntegerField(help_text='Programs Id.', unique=True, db_index=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('credentials_service.abstractcertificate',),
        ),
        migrations.AddField(
            model_name='abstractcertificate',
            name='signatory',
            field=models.ForeignKey(to='credentials_service.Signatory'),
        ),
        migrations.AddField(
            model_name='abstractcertificate',
            name='template',
            field=models.ForeignKey(blank=True, to='credentials_service.CertificateTemplate', null=True),
        ),
        migrations.AlterUniqueTogether(
            name='coursecertificate',
            unique_together=set([('course_id', 'certificate_type')]),
        ),
    ]

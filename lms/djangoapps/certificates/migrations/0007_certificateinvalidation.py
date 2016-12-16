# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
from django.conf import settings
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('certificates', '0006_certificatetemplateasset_asset_slug'),
    ]

    operations = [
        migrations.CreateModel(
            name='CertificateInvalidation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('notes', models.TextField(default=None, null=True)),
                ('active', models.BooleanField(default=True)),
                ('generated_certificate', models.ForeignKey(to='certificates.GeneratedCertificate')),
                ('invalidated_by', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]

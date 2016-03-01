# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('credit', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='creditprovider',
            name='provider_id',
            field=models.CharField(help_text='Unique identifier for this credit provider. Only alphanumeric characters and hyphens (-) are allowed. The identifier is case-sensitive.', unique=True, max_length=255, validators=[django.core.validators.RegexValidator(regex=b'[a-z,A-Z,0-9,\\-]+', message=b'Only alphanumeric characters and hyphens (-) are allowed', code=b'invalid_provider_id')]),
        ),
    ]

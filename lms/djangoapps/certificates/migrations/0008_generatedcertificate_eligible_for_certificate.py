# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('certificates', '0007_certificateinvalidation'),
    ]

    operations = [
        migrations.AddField(
            model_name='generatedcertificate',
            name='eligible_for_certificate',
            field=models.BooleanField(default=True),
        ),
    ]

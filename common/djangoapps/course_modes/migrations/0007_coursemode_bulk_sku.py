# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course_modes', '0006_auto_20160208_1407'),
    ]

    operations = [
        migrations.AddField(
            model_name='coursemode',
            name='bulk_sku',
            field=models.CharField(help_text='OPTIONAL: This is the bulk SKU (stock keeping unit) of this mode in the external ecommerce service.  Leave this blank if the course has not yet been migrated to the ecommerce service.', max_length=255, null=True, verbose_name=b'Bulk SKU', blank=True),
        ),
    ]

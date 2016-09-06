# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('site_configuration', '0002_auto_20160720_0231'),
    ]

    operations = [
        migrations.AddField(
            model_name='siteconfiguration',
            name='receipt_page_url',
            field=models.CharField(default=b'/commerce/checkout/receipt/?orderNum=', help_text='Path to order receipt page.', max_length=255),
        ),
    ]

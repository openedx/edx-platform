# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0003_catalogintegration_page_size'),
    ]

    operations = [
        migrations.AlterField(
            model_name='catalogintegration',
            name='internal_api_url',
            field=models.URLField(help_text='DEPRECATED: Use the setting COURSE_CATALOG_API_URL.', verbose_name='Internal API URL'),
        ),
    ]

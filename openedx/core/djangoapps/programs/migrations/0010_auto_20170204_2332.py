# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('programs', '0009_programsapiconfig_marketing_path'),
    ]

    operations = [
        migrations.AlterField(
            model_name='programsapiconfig',
            name='internal_service_url',
            field=models.URLField(verbose_name='Internal Service URL', blank=True),
        ),
        migrations.AlterField(
            model_name='programsapiconfig',
            name='public_service_url',
            field=models.URLField(verbose_name='Public Service URL', blank=True),
        ),
    ]

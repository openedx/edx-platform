# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('credentials', '0002_auto_20160325_0631'),
    ]

    operations = [
        migrations.AlterField(
            model_name='credentialsapiconfig',
            name='internal_service_url',
            field=models.URLField(help_text=u'DEPRECATED: Use the setting CREDENTIALS_INTERNAL_SERVICE_URL.', verbose_name='Internal Service URL'),
        ),
        migrations.AlterField(
            model_name='credentialsapiconfig',
            name='public_service_url',
            field=models.URLField(help_text=u'DEPRECATED: Use the setting CREDENTIALS_PUBLIC_SERVICE_URL.', verbose_name='Public Service URL'),
        ),
    ]

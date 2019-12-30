# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('programs', '0003_auto_20151120_1613'),
    ]

    operations = [
        migrations.AddField(
            model_name='programsapiconfig',
            name='enable_certification',
            field=models.BooleanField(default=False, verbose_name='Enable Program Certificate Generation'),
        ),
    ]

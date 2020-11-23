# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ccxcon', '0001_initial_ccxcon_model'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='ccxcon',
            options={'verbose_name': 'CCX Connector', 'verbose_name_plural': 'CCX Connectors'},
        ),
    ]

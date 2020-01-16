# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courseware', '0002_coursedynamicupgradedeadlineconfiguration_dynamicupgradedeadlineconfiguration'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coursedynamicupgradedeadlineconfiguration',
            name='opt_out',
            field=models.BooleanField(default=False, help_text='This does not do anything and is no longer used. Setting enabled=False has the same effect.'),
        ),
    ]

# -*- coding: utf-8 -*-


from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('xblock_django', '0003_add_new_config_models'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='xblockdisableconfig',
            name='changed_by',
        ),
        migrations.DeleteModel(
            name='XBlockDisableConfig',
        ),
    ]

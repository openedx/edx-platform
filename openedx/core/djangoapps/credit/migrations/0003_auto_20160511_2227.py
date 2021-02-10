# -*- coding: utf-8 -*-


from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('credit', '0002_creditconfig'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='creditrequirementstatus',
            options={'verbose_name_plural': 'Credit requirement statuses'},
        ),
    ]

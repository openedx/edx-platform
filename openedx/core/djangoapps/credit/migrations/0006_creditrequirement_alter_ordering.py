# -*- coding: utf-8 -*-


from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('credit', '0005_creditrequirement_sort_value'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='creditrequirement',
            options={'ordering': ['sort_value']},
        ),
    ]

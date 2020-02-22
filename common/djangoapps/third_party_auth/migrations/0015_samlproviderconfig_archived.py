# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('third_party_auth', '0014_auto_20171222_1233'),
    ]

    operations = [
        migrations.AddField(
            model_name='samlproviderconfig',
            name='archived',
            field=models.BooleanField(default=False),
        ),
    ]

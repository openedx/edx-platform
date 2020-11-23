# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api_admin', '0005_auto_20160414_1232'),
    ]

    operations = [
        migrations.CreateModel(
            name='Catalog',
            fields=[
                ('id', models.IntegerField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('query', models.TextField()),
                ('viewers', models.TextField()),
            ],
            options={
                'managed': False,
            },
        ),
    ]

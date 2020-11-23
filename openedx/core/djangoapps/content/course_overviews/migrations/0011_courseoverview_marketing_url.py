# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course_overviews', '0010_auto_20160329_2317'),
    ]

    operations = [
        migrations.AddField(
            model_name='courseoverview',
            name='marketing_url',
            field=models.TextField(null=True),
        ),
    ]

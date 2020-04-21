# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course_modes', '0002_coursemode_expiration_datetime_is_explicit'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coursemode',
            name='expiration_datetime_is_explicit',
            field=models.BooleanField(default=False),
        ),
    ]

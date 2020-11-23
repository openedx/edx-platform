# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0003_auto_20160516_0938'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='profile_image_uploaded_at',
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]

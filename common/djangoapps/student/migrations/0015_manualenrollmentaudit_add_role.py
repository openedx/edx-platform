# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0014_courseenrollmentallowed_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='manualenrollmentaudit',
            name='role',
            field=models.CharField(max_length=64, null=True, blank=True),
        ),
    ]

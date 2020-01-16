# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schedules', '0004_auto_20170922_1428'),
    ]

    operations = [
        migrations.AddField(
            model_name='scheduleconfig',
            name='deliver_course_update',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='scheduleconfig',
            name='enqueue_course_update',
            field=models.BooleanField(default=False),
        ),
    ]

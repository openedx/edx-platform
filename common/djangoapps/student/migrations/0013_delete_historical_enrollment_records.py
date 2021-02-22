# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0012_sociallink'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='historicalcourseenrollment',
            name='course',
        ),
        migrations.RemoveField(
            model_name='historicalcourseenrollment',
            name='history_user',
        ),
        migrations.RemoveField(
            model_name='historicalcourseenrollment',
            name='user',
        ),
        migrations.DeleteModel(
            name='HistoricalCourseEnrollment',
        ),
    ]

# -*- coding: utf-8 -*-


from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('course_overviews', '0004_courseoverview_org'),
    ]

    operations = [
        migrations.DeleteModel(
            name='CourseOverviewGeneratedHistory',
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0007_arbisoft_candidate'),
    ]

    operations = [
        migrations.AlterField(
            model_name='candidatecourse',
            name='studied_course',
            field=models.CharField(default=b'Programming', max_length=255, choices=[(b'Programming', b'Programming'), (b'Object Oriented Programming', b'Object Oriented Programming'), (b'Data Structures', b'Data Structures'), (b'Software Engineering', b'Software Engineering'), (b'Artificial Intelligence', b'Artificial Intelligence'), (b'Databases', b'Databases'), (b'Operating System', b'Operating System'), (b'Algorithms', b'Algorithms')]),
        ),
        migrations.AlterField(
            model_name='candidateexpertise',
            name='expertise',
            field=models.CharField(default=b'Programming', max_length=255, choices=[(b'Programming', b'Programming'), (b'Object Oriented Programming', b'Object Oriented Programming'), (b'Data Structures', b'Data Structures'), (b'Software Engineering', b'Software Engineering'), (b'Artificial Intelligence', b'Artificial Intelligence'), (b'Databases', b'Databases'), (b'Operating System', b'Operating System'), (b'Algorithms', b'Algorithms')]),
        ),
        migrations.AlterField(
            model_name='candidateprofile',
            name='position_in_class',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='candidatetechnology',
            name='technology',
            field=models.CharField(default=b'Web Development', max_length=255, choices=[(b'Web Development', b'Web Development'), (b'Mobile Development (Android)', b'Mobile Development (Android)'), (b'Mobile Development (iOS)', b'Mobile Development (iOS)'), (b'Data Science / Machine Learning', b'Data Science / Machine Learning')]),
        ),
    ]

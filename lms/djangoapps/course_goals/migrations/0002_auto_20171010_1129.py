# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course_goals', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coursegoal',
            name='goal_key',
            field=models.CharField(default=b'unsure', max_length=100, choices=[(b'certify', 'Earn a certificate'), (b'complete', 'Complete the course'), (b'explore', 'Explore the course'), (b'unsure', 'Not sure yet')]),
        ),
    ]

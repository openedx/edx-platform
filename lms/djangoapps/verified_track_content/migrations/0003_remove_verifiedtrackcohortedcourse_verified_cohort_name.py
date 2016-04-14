# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('verified_track_content', '0002_verifiedtrackcohortedcourse_verified_cohort_name'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='verifiedtrackcohortedcourse',
            name='verified_cohort_name',
        ),
    ]

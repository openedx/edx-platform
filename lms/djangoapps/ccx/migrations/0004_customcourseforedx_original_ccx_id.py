# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ccx', '0003_add_master_course_staff_in_ccx'),
    ]

    operations = [
        migrations.AddField(
            model_name='customcourseforedx',
            name='original_ccx_id',
            field=models.IntegerField(default=0, verbose_name=b'ID of original CCX course entry'),
            preserve_default=False,
        ),
    ]

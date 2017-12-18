# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course_modes', '0004_auto_20151113_1457'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                    migrations.RemoveField(
                        model_name='coursemode',
                        name='expiration_datetime',
                    ),
                    migrations.AddField(
                        model_name='coursemode',
                        name='_expiration_datetime',
                        field=models.DateTimeField(db_column=b'expiration_datetime', default=None, blank=True, help_text='OPTIONAL: After this date/time, users will no longer be able to enroll in this mode. Leave this blank if users can enroll in this mode until enrollment closes for the course.', null=True, verbose_name='Upgrade Deadline'),
                    ),
            ]
        )
    ]

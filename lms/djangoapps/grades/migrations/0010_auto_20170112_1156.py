# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('grades', '0009_auto_20170111_1507'),
    ]

    operations = [
        migrations.AlterIndexTogether(
            name='persistentsubsectiongrade',
            index_together=set([('modified', 'course_id', 'usage_key'), ('first_attempted', 'course_id', 'user_id')]),
        ),
    ]

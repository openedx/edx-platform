# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('verify_student', '0003_auto_20151113_1443'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='historicalverificationdeadline',
            name='history_user',
        ),
        migrations.DeleteModel(
            name='HistoricalVerificationDeadline',
        ),
    ]

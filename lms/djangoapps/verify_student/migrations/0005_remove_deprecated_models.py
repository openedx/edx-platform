# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('verify_student', '0004_delete_historical_records'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='icrvstatusemailsconfiguration',
            name='changed_by',
        ),
        migrations.RemoveField(
            model_name='incoursereverificationconfiguration',
            name='changed_by',
        ),
        migrations.AlterUniqueTogether(
            name='skippedreverification',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='skippedreverification',
            name='checkpoint',
        ),
        migrations.RemoveField(
            model_name='skippedreverification',
            name='user',
        ),
        migrations.AlterUniqueTogether(
            name='verificationcheckpoint',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='verificationcheckpoint',
            name='photo_verification',
        ),
        migrations.RemoveField(
            model_name='verificationstatus',
            name='checkpoint',
        ),
        migrations.RemoveField(
            model_name='verificationstatus',
            name='user',
        ),
        migrations.DeleteModel(
            name='IcrvStatusEmailsConfiguration',
        ),
        migrations.DeleteModel(
            name='InCourseReverificationConfiguration',
        ),
        migrations.DeleteModel(
            name='SkippedReverification',
        ),
        migrations.DeleteModel(
            name='VerificationCheckpoint',
        ),
        migrations.DeleteModel(
            name='VerificationStatus',
        ),
    ]

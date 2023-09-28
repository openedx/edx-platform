from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schedules', '0005_auto_20171010_1722'),
    ]

    operations = [
        migrations.CreateModel(
            name='ScheduleExperience',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('experience_type', models.PositiveSmallIntegerField(default=0, choices=[(0, 'Recurring Nudge and Upgrade Reminder'), (1, 'Course Updates')])),
                ('schedule', models.OneToOneField(related_name='experience', to='schedules.Schedule', on_delete=models.CASCADE)),
            ],
        ),
    ]

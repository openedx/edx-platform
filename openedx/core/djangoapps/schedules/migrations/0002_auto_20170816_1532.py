from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schedules', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='schedule',
            name='start',
            field=models.DateTimeField(help_text='Date this schedule went into effect', db_index=True),
        ),
        migrations.AlterField(
            model_name='schedule',
            name='upgrade_deadline',
            field=models.DateTimeField(help_text='Deadline by which the learner must upgrade to a verified seat', null=True, db_index=True, blank=True),
        ),
    ]

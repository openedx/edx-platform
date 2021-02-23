from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('grades', '0007_add_passed_timestamp_column'),
    ]

    operations = [
        migrations.AddField(
            model_name='persistentsubsectiongrade',
            name='first_attempted',
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]

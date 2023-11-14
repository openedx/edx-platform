

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0046_survey_form'),
    ]

    operations = [
        migrations.AddField(
            model_name='UserProfile',
            name='organization',
            field=models.CharField(max_length=255, default=''),
        ),
    ]

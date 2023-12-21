

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0049_user_lab_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='UserProfile',
            name='organization',
            field=models.CharField(max_length=255, default=''),
        ),
    ]

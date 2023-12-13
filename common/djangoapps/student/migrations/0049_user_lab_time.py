

from django.db import migrations, models
import django.utils.timezone

class Migration(migrations.Migration):

    dependencies = [
        ('student', '0048_user_lab'),
    ]

    operations = [
        migrations.AddField(
            model_name='StudentLab',
            name='date',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False),
        ),
    ]

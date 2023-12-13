

from django.db import migrations, models
import django.utils.timezone

class Migration(migrations.Migration):

    dependencies = [
        ('upload_file', '0001_inital_'),
    ]

    operations = [
        migrations.AddField(
            model_name='UploadFile',
            name='date',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False),
        ),
    ]

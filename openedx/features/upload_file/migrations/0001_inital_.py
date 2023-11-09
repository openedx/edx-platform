

from django.db import migrations, models
from openedx.features.upload_file.models import attachment_file_name

class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='UploadFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=250)),
                ('block_id', models.CharField(max_length=255)),
                ('course_id', models.CharField(max_length=255)),
                ('type', models.CharField(max_length=255)),
                ('file', models.FileField(upload_to=attachment_file_name)),
            ],
        )
        
    ]
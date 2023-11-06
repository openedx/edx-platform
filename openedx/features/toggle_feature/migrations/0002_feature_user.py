from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings

class Migration(migrations.Migration):

    dependencies = [
        ('toggle_feature', '0001_inital'),
    ]

    operations = [
       migrations.CreateModel(
            name='ToggleFeatureUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('student', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
                ('is_feedback' , models.BooleanField(default=True)),
                ('is_discussion' , models.BooleanField(default=True)),
                ('is_date_and_progress' , models.BooleanField(default=True)),
                ('is_search', models.BooleanField(default=True)),
                ('is_chatGPT', models.BooleanField(default=True)),
            ]
        
        ),
    ]

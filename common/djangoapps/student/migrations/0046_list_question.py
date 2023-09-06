from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('student', '0045_last_history_activte_course'),
    ]

    operations = [
        migrations.CreateModel(
            name='listSurveyQuestion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('survey_id' , models.IntegerField()),
                ('question', models.CharField( max_length=255, null=True)),
                ('type', models.CharField( max_length=255, null=True)),
                ('config', models.JSONField(null=True))
            ],
           options={
                'ordering': ('question'),
            },
        ),
        
    
    ]
    

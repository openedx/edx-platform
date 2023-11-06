from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings
from opaque_keys.edx.django.models import CourseKeyField


class Migration(migrations.Migration):
    initial = True

    operations = [
        migrations.CreateModel(
            name='ToggleFeatureCourse',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('course_id', CourseKeyField(max_length=255, db_index=True)),
                ('is_feedback' , models.BooleanField(default=True)),
                ('is_discussion' , models.BooleanField(default=True)),
                ('is_date_and_progress' , models.BooleanField(default=True)),
                ('is_search', models.BooleanField(default=True)),
                ('is_chatGPT', models.BooleanField(default=True)),
                ('changed_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='Changed by')),
            ]
        
        ),
    ]

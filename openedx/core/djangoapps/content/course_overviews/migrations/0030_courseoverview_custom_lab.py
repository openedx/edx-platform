

from django.conf import settings
from django.db import migrations, models



class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
          ('course_overviews', '00029_courseoverview_results_lab'),
    ]

    operations = [
        migrations.AddField(
            model_name='CourseResultLab',
            name='type_lab',
            field=models.CharField(max_length=20),
        )
    ]










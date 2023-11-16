

from django.conf import settings
from django.db import migrations, models



class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
          ('course_overviews', '0028_courseoverview_courseunittime'),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseResultLab',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('block_id' , models.CharField(max_length=255)),
                ('course_id', models.CharField(max_length=255)),
                ('result', models.TextField(default='')),

            ],
        )
    ]










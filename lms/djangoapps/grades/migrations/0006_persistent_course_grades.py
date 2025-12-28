import django.utils.timezone
import model_utils.fields
from django.db import migrations, models
from opaque_keys.edx.django.models import CourseKeyField

from lms.djangoapps.courseware.fields import UnsignedBigIntAutoField


class Migration(migrations.Migration):

    dependencies = [
        ('grades', '0005_multiple_course_flags'),
    ]

    operations = [
        migrations.CreateModel(
            name='PersistentCourseGrade',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('id', UnsignedBigIntAutoField(serialize=False, primary_key=True)),
                ('user_id', models.IntegerField(db_index=True)),
                ('course_id', CourseKeyField(max_length=255)),
                ('course_edited_timestamp', models.DateTimeField(verbose_name='Last content edit timestamp')),
                ('course_version', models.CharField(max_length=255, verbose_name='Course content version identifier', blank=True)),
                ('grading_policy_hash', models.CharField(max_length=255, verbose_name='Hash of grading policy')),
                ('percent_grade', models.FloatField()),
                ('letter_grade', models.CharField(max_length=255, verbose_name='Letter grade for course')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='persistentcoursegrade',
            unique_together={('course_id', 'user_id')},
        ),
    ]

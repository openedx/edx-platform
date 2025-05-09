from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('grades', '0006_persistent_course_grades'),
    ]

    operations = [
        migrations.AddField(
            model_name='persistentcoursegrade',
            name='passed_timestamp',
            field=models.DateTimeField(null=True, verbose_name='Date learner earned a passing grade', blank=True),
        ),

    ]

from django.db import migrations, models
from opaque_keys.edx.django.models import CourseKeyField


class Migration(migrations.Migration):

    dependencies = [
        ('course_groups', '0002_change_inline_default_cohort_value'),
    ]

    operations = [
        migrations.CreateModel(
            name='UnregisteredLearnerCohortAssignments',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('email', models.CharField(db_index=True, max_length=255, blank=True)),
                ('course_id', CourseKeyField(max_length=255)),
                ('course_user_group', models.ForeignKey(to='course_groups.CourseUserGroup', on_delete=models.CASCADE)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='unregisteredlearnercohortassignments',
            unique_together={('course_id', 'email')},
        ),
    ]

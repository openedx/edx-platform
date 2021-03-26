from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course_modes', '0007_coursemode_bulk_sku'),
        ('bulk_email', '0005_move_target_data'),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseModeTarget',
            fields=[
                ('target_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='bulk_email.Target', on_delete=models.CASCADE)),
                ('track', models.ForeignKey(to='course_modes.CourseMode', on_delete=models.CASCADE)),
            ],
            bases=('bulk_email.target',),
        ),
        migrations.AlterField(
            model_name='target',
            name='target_type',
            field=models.CharField(max_length=64, choices=[('myself', 'Myself'), ('staff', 'Staff and instructors'), ('learners', 'All students'), ('cohort', 'Specific cohort'), ('track', 'Specific course mode')]),
        ),
    ]

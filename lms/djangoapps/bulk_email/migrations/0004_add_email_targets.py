# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course_groups', '0001_initial'),
        ('bulk_email', '0003_config_model_feature_flag'),
    ]

    operations = [
        migrations.CreateModel(
            name='Target',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('target_type', models.CharField(max_length=64, choices=[(u'myself', u'Myself'), (u'staff', u'Staff and instructors'), (u'learners', u'All students'), (u'cohort', u'Specific cohort')])),
            ],
        ),
        migrations.AlterField(
            model_name='courseemail',
            name='to_option',
            field=models.CharField(max_length=64, choices=[(u'deprecated', u'deprecated')]),
        ),
        migrations.CreateModel(
            name='CohortTarget',
            fields=[
                ('target_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='bulk_email.Target', on_delete=models.CASCADE)),
                ('cohort', models.ForeignKey(to='course_groups.CourseUserGroup', on_delete=models.CASCADE)),
            ],
            bases=('bulk_email.target',),
        ),
        migrations.AddField(
            model_name='courseemail',
            name='targets',
            field=models.ManyToManyField(to='bulk_email.Target'),
        ),
    ]

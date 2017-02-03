# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('student', '0006_logoutviewconfiguration'),
    ]

    operations = [
        migrations.CreateModel(
            name='CandidateCourse',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('studied_course', models.CharField(max_length=255, choices=[(b'Introduction to computing', b'Introduction to computing'), (b'Programming', b'Programming'), (b'Object oriented programming', b'Object oriented programming'), (b'Data Structures', b'Data Structures'), (b'Computer Organization and Assembly Language', b'Computer Organization and Assembly Language'), (b'Software Engineering', b'Software Engineering'), (b'Computer networks', b'Computer networks'), (b'Artificial intelligence', b'Artificial intelligence'), (b'Databases', b'Databases'), (b'Operating System', b'Operating System'), (b'Algorithms', b'Algorithms'), (b'Bio-Informatics', b'Bio-Informatics'), (b'Other', b'Other')])),
            ],
        ),
        migrations.CreateModel(
            name='CandidateExpertise',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('expertise', models.CharField(max_length=255, choices=[(b'Introduction to computing', b'Introduction to computing'), (b'Programming', b'Programming'), (b'Object oriented programming', b'Object oriented programming'), (b'Data Structures', b'Data Structures'), (b'Computer Organization and Assembly Language', b'Computer Organization and Assembly Language'), (b'Software Engineering', b'Software Engineering'), (b'Computer networks', b'Computer networks'), (b'Artificial intelligence', b'Artificial intelligence'), (b'Databases', b'Databases'), (b'Operating System', b'Operating System'), (b'Algorithms', b'Algorithms'), (b'Bio-Informatics', b'Bio-Informatics')])),
                ('rank', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='CandidateProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('graduation_date', models.DateTimeField()),
                ('phone_number', models.CharField(max_length=20)),
                ('cgpa', models.DecimalField(max_digits=4, decimal_places=2)),
                ('position_in_class', models.CharField(max_length=25)),
                ('academic_projects', models.CharField(max_length=255)),
                ('extra_curricular_activities', models.CharField(max_length=255)),
                ('freelance_work', models.CharField(max_length=255)),
                ('accomplishment', models.CharField(max_length=255)),
                ('individuality_factor', models.CharField(max_length=255)),
                ('ideal_organization', models.CharField(max_length=255)),
                ('why_arbisoft', models.CharField(max_length=255)),
                ('expected_salary', models.IntegerField()),
                ('career_plan', models.CharField(max_length=255)),
                ('references', models.CharField(max_length=255)),
                ('other_studied_course', models.CharField(max_length=255, null=True, blank=True)),
                ('other_technology', models.CharField(max_length=255, null=True, blank=True)),
                ('user', models.OneToOneField(related_name='arbisoft_profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='CandidateTechnology',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('technology', models.CharField(max_length=255, choices=[(b'Python/Django', b'Python/Django'), (b'Scrappy/Data Science', b'Scrappy/Data Science'), (b'Android', b'Android'), (b'iOS', b'iOS'), (b'PHP', b'PHP'), (b'Javascript', b'Javascript'), (b'Other', b'Other')])),
                ('candidate', models.ForeignKey(to='student.CandidateProfile', null=True)),
            ],
        ),
        migrations.AddField(
            model_name='candidateexpertise',
            name='candidate',
            field=models.ForeignKey(to='student.CandidateProfile', null=True),
        ),
        migrations.AddField(
            model_name='candidatecourse',
            name='candidate',
            field=models.ForeignKey(to='student.CandidateProfile', null=True),
        ),
    ]

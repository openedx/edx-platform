# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import model_utils.fields
import xmodule_django.models
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='OfflineComputedGrade',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('course_id', xmodule_django.models.CourseKeyField(max_length=255, db_index=True)),
                ('created', models.DateTimeField(db_index=True, auto_now_add=True, null=True)),
                ('updated', models.DateTimeField(auto_now=True, db_index=True)),
                ('gradeset', models.TextField(null=True, blank=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='OfflineComputedGradeLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('course_id', xmodule_django.models.CourseKeyField(max_length=255, db_index=True)),
                ('created', models.DateTimeField(db_index=True, auto_now_add=True, null=True)),
                ('seconds', models.IntegerField(default=0)),
                ('nstudents', models.IntegerField(default=0)),
            ],
            options={
                'ordering': ['-created'],
                'get_latest_by': 'created',
            },
        ),
        migrations.CreateModel(
            name='StudentFieldOverride',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('course_id', xmodule_django.models.CourseKeyField(max_length=255, db_index=True)),
                ('location', xmodule_django.models.LocationKeyField(max_length=255, db_index=True)),
                ('field', models.CharField(max_length=255)),
                ('value', models.TextField(default=b'null')),
                ('student', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='StudentModule',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('module_type', models.CharField(default=b'problem', max_length=32, db_index=True, choices=[(b'problem', b'problem'), (b'video', b'video'), (b'html', b'html'), (b'course', b'course'), (b'chapter', b'Section'), (b'sequential', b'Subsection'), (b'library_content', b'Library Content')])),
                ('module_state_key', xmodule_django.models.LocationKeyField(max_length=255, db_column=b'module_id', db_index=True)),
                ('course_id', xmodule_django.models.CourseKeyField(max_length=255, db_index=True)),
                ('state', models.TextField(null=True, blank=True)),
                ('grade', models.FloatField(db_index=True, null=True, blank=True)),
                ('max_grade', models.FloatField(null=True, blank=True)),
                ('done', models.CharField(default=b'na', max_length=8, db_index=True, choices=[(b'na', b'NOT_APPLICABLE'), (b'f', b'FINISHED'), (b'i', b'INCOMPLETE')])),
                ('created', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, db_index=True)),
                ('student', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='StudentModuleHistory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('version', models.CharField(db_index=True, max_length=255, null=True, blank=True)),
                ('created', models.DateTimeField(db_index=True)),
                ('state', models.TextField(null=True, blank=True)),
                ('grade', models.FloatField(null=True, blank=True)),
                ('max_grade', models.FloatField(null=True, blank=True)),
                ('student_module', models.ForeignKey(to='courseware.StudentModule')),
            ],
            options={
                'get_latest_by': 'created',
            },
        ),
        migrations.CreateModel(
            name='XModuleStudentInfoField',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('field_name', models.CharField(max_length=64, db_index=True)),
                ('value', models.TextField(default=b'null')),
                ('created', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, db_index=True)),
                ('student', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='XModuleStudentPrefsField',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('field_name', models.CharField(max_length=64, db_index=True)),
                ('value', models.TextField(default=b'null')),
                ('created', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, db_index=True)),
                ('module_type', xmodule_django.models.BlockTypeKeyField(max_length=64, db_index=True)),
                ('student', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='XModuleUserStateSummaryField',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('field_name', models.CharField(max_length=64, db_index=True)),
                ('value', models.TextField(default=b'null')),
                ('created', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, db_index=True)),
                ('usage_id', xmodule_django.models.LocationKeyField(max_length=255, db_index=True)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='xmoduleuserstatesummaryfield',
            unique_together=set([('usage_id', 'field_name')]),
        ),
        migrations.AlterUniqueTogether(
            name='xmodulestudentprefsfield',
            unique_together=set([('student', 'module_type', 'field_name')]),
        ),
        migrations.AlterUniqueTogether(
            name='xmodulestudentinfofield',
            unique_together=set([('student', 'field_name')]),
        ),
        migrations.AlterUniqueTogether(
            name='studentmodule',
            unique_together=set([('student', 'module_state_key', 'course_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='studentfieldoverride',
            unique_together=set([('course_id', 'field', 'location', 'student')]),
        ),
        migrations.AlterUniqueTogether(
            name='offlinecomputedgrade',
            unique_together=set([('user', 'course_id')]),
        ),
    ]

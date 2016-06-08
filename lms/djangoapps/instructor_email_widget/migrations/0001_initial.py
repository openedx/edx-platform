# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import xmodule_django.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupedQuery',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255)),
                ('course_id', xmodule_django.models.CourseKeyField(max_length=255, db_index=True)),
                ('created', models.DateTimeField(db_index=True, auto_now_add=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='GroupedTempQueryForSubquery',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('grouped', models.ForeignKey(to='instructor_email_widget.GroupedQuery')),
            ],
        ),
        migrations.CreateModel(
            name='SavedQuery',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('course_id', xmodule_django.models.CourseKeyField(max_length=255, db_index=True)),
                ('module_state_key', xmodule_django.models.LocationKeyField(max_length=255, db_column=b'module_id', db_index=True)),
                ('inclusion', models.CharField(max_length=1, choices=[(b'A', b'AND'), (b'N', b'NOT'), (b'O', b'OR')])),
                ('filter_on', models.CharField(max_length=255)),
                ('entity_name', models.CharField(max_length=255)),
                ('query_type', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='StudentsForQuery',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('inclusion', models.CharField(max_length=1, choices=[(b'A', b'AND'), (b'N', b'NOT'), (b'O', b'OR')])),
            ],
        ),
        migrations.CreateModel(
            name='SubqueryForGroupedQuery',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('grouped', models.ForeignKey(to='instructor_email_widget.GroupedQuery')),
                ('query', models.ForeignKey(to='instructor_email_widget.SavedQuery')),
            ],
        ),
        migrations.CreateModel(
            name='TemporaryQuery',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('course_id', xmodule_django.models.CourseKeyField(max_length=255, db_index=True)),
                ('module_state_key', xmodule_django.models.LocationKeyField(max_length=255, db_column=b'module_id', db_index=True)),
                ('inclusion', models.CharField(max_length=1, choices=[(b'A', b'AND'), (b'N', b'NOT'), (b'O', b'OR')])),
                ('filter_on', models.CharField(max_length=255)),
                ('created', models.DateTimeField(db_index=True, auto_now_add=True, null=True)),
                ('entity_name', models.CharField(max_length=255)),
                ('query_type', models.CharField(max_length=255)),
                ('origin', models.CharField(default=b'W', max_length=1, choices=[(b'E', b'EMAIL'), (b'W', b'WIDGET')])),
                ('done', models.NullBooleanField()),
            ],
        ),
        migrations.AddField(
            model_name='studentsforquery',
            name='query',
            field=models.ForeignKey(to='instructor_email_widget.TemporaryQuery'),
        ),
        migrations.AddField(
            model_name='studentsforquery',
            name='student',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='groupedtempqueryforsubquery',
            name='query',
            field=models.ForeignKey(to='instructor_email_widget.TemporaryQuery'),
        ),
    ]

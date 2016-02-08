# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import courseware.fields
from django.conf import settings


def bump_pk_start(apps, schema_editor):
    if not schema_editor.connection.alias == 'student_module_history':
                return
    StudentModuleHistory = apps.get_model("courseware", "StudentModuleHistory")
    initial_id = settings.STUDENTMODULEHISTORYEXTENDED_OFFSET + StudentModuleHistory.objects.all().latest('id').id

    if schema_editor.connection.vendor == 'mysql':
        schema_editor.execute('ALTER TABLE courseware_studentmodulehistoryextended AUTO_INCREMENT=%s', [initial_id])
    elif schema_editor.connection.vendor == 'sqlite3':
        # This is a hack to force sqlite to add new rows after the earlier rows we
        # want to migrate.
        StudentModuleHistory(
            id=initial_id,
            course_key=None,
            usage_key=None,
            username="",
            version="",
            created=datetime.datetime.now(),
        ).save()


class Migration(migrations.Migration):

    dependencies = [
        ('courseware', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='StudentModuleHistoryExtended',
            fields=[
                ('id', courseware.fields.UnsignedBigIntAutoField(serialize=False, primary_key=True)),
                ('version', models.CharField(db_index=True, max_length=255, null=True, blank=True)),
                ('created', models.DateTimeField(db_index=True)),
                ('state', models.TextField(null=True, blank=True)),
                ('grade', models.FloatField(null=True, blank=True)),
                ('max_grade', models.FloatField(null=True, blank=True)),
                ('student_module', models.ForeignKey(to='courseware.StudentModule', db_constraint=False)),
            ],
            options={
                'get_latest_by': 'created',
            },
        ),
        migrations.RunPython(bump_pk_start, reverse_code=migrations.RunPython.noop),
    ]

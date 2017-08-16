# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import openedx.core.djangoapps.xmodule_django.models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('courseware', '0002_coursedynamicupgradedeadlineconfiguration_dynamicupgradedeadlineconfiguration'),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseScheduleConfiguration',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('change_date', models.DateTimeField(auto_now_add=True, verbose_name='Change date')),
                ('enabled', models.BooleanField(default=False, verbose_name='Enabled')),
                ('course_id', openedx.core.djangoapps.xmodule_django.models.CourseKeyField(max_length=255, db_index=True)),
                ('verified_upgrade_deadline_days', models.PositiveSmallIntegerField(default=21, help_text='Number of days a learner has to upgrade after content is made available')),
                ('verified_upgrade_deadline_enabled', models.BooleanField(default=False, help_text='Should this course display an upgrade deadline to users. Only applies to courses with schedules.')),
                ('verified_upgrade_reminder_message_enabled', models.BooleanField(default=False, help_text='Should we send verified upgrade reminder messages to users in this course.')),
                ('recurring_reminder_message_enabled', models.BooleanField(default=False, help_text='Should we send recurring nudge messages to users in this course.')),
                ('changed_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='Changed by')),
            ],
        ),
    ]

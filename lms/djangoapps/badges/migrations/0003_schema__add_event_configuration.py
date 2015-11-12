# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('badges', '0002_data__migrate_assertions'),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseEventBadgesConfiguration',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('change_date', models.DateTimeField(auto_now_add=True, verbose_name='Change date')),
                ('enabled', models.BooleanField(default=False, verbose_name='Enabled')),
                ('courses_completed', models.TextField(default=b'', help_text="On each line, put the number of completed courses to award a badge for, a comma, and the slug of a badge class you have created with the issuing component 'edx__course'. For example: 3,course-v1:edx/Demo/DemoX", blank=True)),
                ('courses_enrolled', models.TextField(default=b'', help_text="On each line, put the number of enrolled courses to award a badge for, a comma, and the slug of a badge class you have created with the issuing component 'edx__course'. For example: 3,course-v1:edx/Demo/DemoX", blank=True)),
                ('course_groups', models.TextField(default=b'', help_text="On each line, put the slug of a badge class you have created with the issuing component 'edx__course' to award, a comma, and a comma separated list of course keys that the user will need to complete to get this badge. For example: slug_for_compsci_courses_group_badge,course-v1:CompSci+Course+First,course-v1:CompsSci+Course+Second", blank=True)),
                ('changed_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='Changed by')),
            ],
        ),
        migrations.AlterModelOptions(
            name='badgeclass',
            options={'verbose_name_plural': 'Badge Classes'},
        ),
    ]

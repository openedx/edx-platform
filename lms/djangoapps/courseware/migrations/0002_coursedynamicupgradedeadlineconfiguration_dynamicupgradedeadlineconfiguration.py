# -*- coding: utf-8 -*-


import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
from opaque_keys.edx.django.models import CourseKeyField


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('courseware', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseDynamicUpgradeDeadlineConfiguration',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('change_date', models.DateTimeField(auto_now_add=True, verbose_name='Change date')),
                ('enabled', models.BooleanField(default=False, verbose_name='Enabled')),
                ('course_id', CourseKeyField(max_length=255, db_index=True)),
                ('deadline_days', models.PositiveSmallIntegerField(default=21, help_text='Number of days a learner has to upgrade after content is made available')),
                ('opt_out', models.BooleanField(default=False, help_text='Disable the dynamic upgrade deadline for this course run.')),
                ('changed_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='Changed by')),
            ],
        ),
        migrations.CreateModel(
            name='DynamicUpgradeDeadlineConfiguration',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('change_date', models.DateTimeField(auto_now_add=True, verbose_name='Change date')),
                ('enabled', models.BooleanField(default=False, verbose_name='Enabled')),
                ('deadline_days', models.PositiveSmallIntegerField(default=21, help_text='Number of days a learner has to upgrade after content is made available')),
                ('changed_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='Changed by')),
            ],
        ),
    ]

# -*- coding: utf-8 -*-


from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings
from opaque_keys.edx.django.models import CourseKeyField


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('verified_track_content', '0002_verifiedtrackcohortedcourse_verified_cohort_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='MigrateVerifiedTrackCohortsSetting',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('change_date', models.DateTimeField(auto_now_add=True, verbose_name='Change date')),
                ('enabled', models.BooleanField(default=False, verbose_name='Enabled')),
                ('old_course_key', CourseKeyField(help_text=u'Course key for which to migrate verified track cohorts from', max_length=255)),
                ('rerun_course_key', CourseKeyField(help_text=u'Course key for which to migrate verified track cohorts to enrollment tracks to', max_length=255)),
                ('audit_cohort_names', models.TextField(help_text=u'Comma-separated list of audit cohort names')),
                ('changed_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='Changed by')),
            ],
        ),
    ]

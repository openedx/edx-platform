# -*- coding: utf-8 -*-



import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
from opaque_keys.edx.django.models import CourseKeyField


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='WaffleFlagCourseOverrideModel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('change_date', models.DateTimeField(auto_now_add=True, verbose_name='Change date')),
                ('enabled', models.BooleanField(default=False, verbose_name='Enabled')),
                ('waffle_flag', models.CharField(max_length=255, db_index=True)),
                ('course_id', CourseKeyField(max_length=255, db_index=True)),
                ('override_choice', models.CharField(default=u'on', max_length=3, choices=[(u'on', u'Force On'), (u'off', u'Force Off')])),
                ('changed_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='Changed by')),
            ],
            options={
                'verbose_name': 'Waffle flag course override',
                'verbose_name_plural': 'Waffle flag course overrides',
            },
        ),
    ]

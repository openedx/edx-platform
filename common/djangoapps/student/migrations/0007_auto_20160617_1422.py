# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('course_modes', '0008_auto_20160617_1422'),
        ('student', '0006_logoutviewconfiguration'),
    ]

    operations = [
        migrations.AddField(
            model_name='courseenrollment',
            name='course_mode',
            field=models.ForeignKey(verbose_name='Course Mode', blank=True, to='course_modes.CourseMode', null=True),
        ),
        migrations.AddField(
            model_name='courseenrollment',
            name='modified',
            field=model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False),
        ),
        migrations.AddField(
            model_name='historicalcourseenrollment',
            name='course_mode',
            field=models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.DO_NOTHING, db_constraint=False, blank=True, to='course_modes.CourseMode', null=True),
        ),
        migrations.AddField(
            model_name='historicalcourseenrollment',
            name='modified',
            field=model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False),
        ),
        migrations.AlterField(
            model_name='courseenrollment',
            name='created',
            field=model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False),
        ),
        migrations.AlterField(
            model_name='historicalcourseenrollment',
            name='created',
            field=model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False),
        ),
    ]

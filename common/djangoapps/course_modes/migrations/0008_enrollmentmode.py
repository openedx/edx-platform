# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def create_modes(apps, schema_editor):
    """
    Populate the enrollment modes table with our current modes.
    """

    enrollment_mode_model = apps.get_model("course_modes", "EnrollmentMode")

    objects = enrollment_mode_model.objects
    if not objects.exists():
        for mode in ['audit', 'verified', 'professional', 'no-id-professional', 'credit', 'honor']:
            objects.create(mode_slug=mode)


def delete_modes(apps, schema_editor):
    """
    Delete the enrollment modes table data.
    """
    enrollment_mode_model = apps.get_model("course_modes", "EnrollmentMode")
    enrollment_mode_model.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('course_modes', '0007_coursemode_bulk_sku'),
    ]

    operations = [
        migrations.CreateModel(
            name='EnrollmentMode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('mode_slug', models.CharField(unique=True, max_length=100)),
            ],
        ),
        migrations.RunPython(
            code=create_modes,
            reverse_code=delete_modes
        )
    ]

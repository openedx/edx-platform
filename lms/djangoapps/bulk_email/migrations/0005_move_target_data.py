# -*- coding: utf-
from __future__ import unicode_literals

from django.db import migrations, models
from django.db.utils import DatabaseError

def to_option_to_targets(apps, schema_editor):
    CourseEmail = apps.get_model("bulk_email", "CourseEmail")
    db_alias = schema_editor.connection.alias
    try:
        for email in CourseEmail.objects.using(db_alias).all().iterator():
            desired_target_class = CourseEmail.TO_OPTION_CLASS_MAP.get(email.to_option, None)
            if desired_target_class is not None and len(email.targets) == 0:
                email.targets = [
                    desired_target_class.objects.using(db_alias).get_or_create(
                        target_type=email.to_option
                    )
                ]
                email.save()
    except DatabaseError:
        # Student module history table will fail this migration otherwise
        pass

def targets_to_to_option(apps, schema_editor):
    CourseEmail = apps.get_model("bulk_email", "CourseEmail")
    db_alias = schema_editor.connection.alias
    try:
        for email in CourseEmail.objects.using(db_alias).all().iterator():
            # Note this is not a perfect 1:1 backwards migration - targets can hold more information than to_option can.
            # We use the first valid value from targets, or 'myself' if none can be found
            email.to_option = next(
                (
                    t_type for t_type in (
                        target.target_type for target in email.targets
                    ) if t_type in CourseEmail.TO_OPTIONS
                ),
                CourseEmail.MYSELF
            )
            email.save()
    except DatabaseError:
        # Student module history table will fail this migration otherwise
        pass

class Migration(migrations.Migration):

    dependencies = [
        ('bulk_email', '0004_add_email_targets'),
    ]

    operations = [
        migrations.RunPython(to_option_to_targets, targets_to_to_option),
    ]

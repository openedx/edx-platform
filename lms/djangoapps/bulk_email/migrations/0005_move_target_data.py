from django.db import migrations, models
from django.db.utils import DatabaseError

from lms.djangoapps.bulk_email.models import EMAIL_TARGETS, SEND_TO_MYSELF


def to_option_to_targets(apps, schema_editor):
    CourseEmail = apps.get_model("bulk_email", "CourseEmail")
    Target = apps.get_model("bulk_email", "Target")
    db_alias = schema_editor.connection.alias
    try:
        for email in CourseEmail.objects.using(db_alias).all().iterator():
            new_target, created = Target.objects.using(db_alias).get_or_create(
                target_type=email.to_option
            )
            email.targets.add(new_target)
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
                        target.target_type for target in email.targets.all()
                    ) if t_type in EMAIL_TARGETS
                ),
                SEND_TO_MYSELF
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

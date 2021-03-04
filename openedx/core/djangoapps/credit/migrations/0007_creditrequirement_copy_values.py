from django.db import migrations


def copy_column_values(apps, schema_editor):
    """
    Copy the order field into the sort_value field.
    """
    CreditRequirement = apps.get_model('credit', 'CreditRequirement')
    for credit_requirement in CreditRequirement.objects.all():
        credit_requirement.sort_value = credit_requirement.order
        credit_requirement.save()


class Migration(migrations.Migration):

    dependencies = [
        ('credit', '0006_creditrequirement_alter_ordering'),
    ]

    operations = [
        migrations.RunPython(
            copy_column_values,
            reverse_code=migrations.RunPython.noop,  # Allow reverse migrations, but make it a no-op.
        ),
    ]

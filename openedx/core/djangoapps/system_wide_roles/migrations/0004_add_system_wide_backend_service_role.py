from django.db import migrations

from openedx.core.djangoapps.system_wide_roles.constants import BACKEND_SERVICE_ADMIN_ROLE


def create_roles(apps, schema_editor):
    """Create the system wide backend service role if it does not already exist."""
    SystemWideRole = apps.get_model('system_wide_roles', 'SystemWideRole')
    SystemWideRole.objects.update_or_create(name=BACKEND_SERVICE_ADMIN_ROLE)


def delete_roles(apps, schema_editor):
    """Delete the system wide backend service role."""
    SystemWideRole = apps.get_model('system_wide_roles', 'SystemWideRole')
    SystemWideRole.objects.filter(
        name=BACKEND_SERVICE_ADMIN_ROLE
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('system_wide_roles', '0003_systemwideroleassignment_applies_to_all_contexts.py'),
    ]

    operations = [
        migrations.RunPython(create_roles, delete_roles)
    ]

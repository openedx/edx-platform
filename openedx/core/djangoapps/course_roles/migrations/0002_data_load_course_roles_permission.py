import json

from django.core.management import call_command
from django.db import migrations


def load_permissions(apps, schema_editor):
    """Load data from the fixture"""
    course_roles_permission = apps.get_model("course_roles", "CourseRolesPermission")
    if not course_roles_permission.objects.exists():
        call_command("loaddata", "permissions.json")


def remove_permissions(apps, schema_editor):
    course_roles_permission = apps.get_model("course_roles", "CourseRolesPermission")
    permissions = json.loads(open("permissions.json").read())
    for permission in permissions:
        course_roles_permission.objects.filter(name=permission["fields"]["name"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('course_roles', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(load_permissions, remove_permissions),
    ]

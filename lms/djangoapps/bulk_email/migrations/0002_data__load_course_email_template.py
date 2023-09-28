from django.core.management import call_command
from django.db import migrations, models


def forwards(apps, schema_editor):
    """Load data from the fixture"""
    CourseEmailTemplate = apps.get_model("bulk_email", "CourseEmailTemplate")
    if not CourseEmailTemplate.objects.exists():
        call_command("loaddata", "course_email_template.json")

def backwards(apps, schema_editor):
    CourseEmailTemplate = apps.get_model("bulk_email", "CourseEmailTemplate")
    CourseEmailTemplate.objects.all().delete()

class Migration(migrations.Migration):

    dependencies = [
        ('bulk_email', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]

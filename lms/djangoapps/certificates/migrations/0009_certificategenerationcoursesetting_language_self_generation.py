from django.apps import apps
from django.db import migrations, models
from django.db.models import F


def copy_field(apps, schema_editor):
    CertificateGenerationCourseSetting = apps.get_model('certificates', 'CertificateGenerationCourseSetting')
    CertificateGenerationCourseSetting.objects.all().update(self_generation_enabled=F('enabled'))

def undo_copy(apps, schema_editor):
    CertificateGenerationCourseSetting = apps.get_model('certificates', 'CertificateGenerationCourseSetting')
    CertificateGenerationCourseSetting.objects.all().update(enabled=F('self_generation_enabled'))

class Migration(migrations.Migration):
    """
    Adds new field 'language_specific_templates_enabled'.
    Also adds field 'self_generation_enabled' which is a 
    replacement for 'enabled'
    Lastly, copies data from 'enabled' to 'self_generation_enabled'
    """
    dependencies = [
        ('certificates', '0008_schema__remove_badges'),
    ]

    operations = [
        migrations.AddField(
            model_name='certificategenerationcoursesetting',
            name='language_specific_templates_enabled',
            field=models.BooleanField(default=False, help_text="Render translated certificates rather than using the platform's default language. Available translations are controlled by the certificate template."),
        ),
        migrations.AddField(
            model_name='certificategenerationcoursesetting',
            name='self_generation_enabled',
            field=models.BooleanField(default=False, help_text='Allow students to generate their own certificates for the course. Enabling this does NOT affect usage of the management command used for batch certificate generation.'),
        ),
        migrations.AlterField(
            model_name='certificategenerationcoursesetting',
            name='enabled',
            field=models.BooleanField(default=False, help_text='DEPRECATED, please use self_generation_enabled instead.'),
        ),
        migrations.RunPython(copy_field, reverse_code=undo_copy),
    ]

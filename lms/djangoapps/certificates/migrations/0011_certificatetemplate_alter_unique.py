# -*- coding: utf-8 -*-


import logging

from django.db import migrations, models
from opaque_keys.edx.django.models import CourseKeyField
from opaque_keys.edx.keys import CourseKey

log = logging.getLogger(__name__)

def revert_alter_unique(apps, schema_editor):
    CertificateTemplateModel = apps.get_model("certificates", "CertificateTemplate")

    all_unique_templates_ignoring_language = CertificateTemplateModel.objects.values_list(
        "organization_id",
        "course_key",
        "mode").distinct()

    for org_id, course_key, mode in all_unique_templates_ignoring_language:
        key = CourseKey.from_string(course_key) if course_key else CourseKeyField.Empty
        templates = CertificateTemplateModel.objects.filter(organization_id=org_id, course_key=key, mode=mode)
        if templates.count() > 1:  
            # remove all templates past the first (null or default languages are ordered first)
            language_specific_templates = templates.order_by('language')[1:] 
            language_specific_template_ids = language_specific_templates.values_list('id', flat=True)
            for template in language_specific_templates:
                log.info('Deleting template ' + str(template.id) +  ' with details {' +
                    "  name: "+ str(template.name) +
                    "  description: "+ str(template.description) +
                    "  template: "+ str(template.template) +
                    "  organization_id: "+ str(template.organization_id) +
                    "  course_key: "+ str(template.course_key) +
                    "  mode: "+ str(template.mode) +
                    "  is_active: "+ str(template.is_active) +
                    "  language: "+ str(template.language) + " }"
                )
            CertificateTemplateModel.objects.filter(id__in=list(language_specific_template_ids)).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('certificates', '0010_certificatetemplate_language'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='certificatetemplate',
            unique_together=set([('organization_id', 'course_key', 'mode', 'language')]),
        ),
        migrations.RunPython(migrations.RunPython.noop, reverse_code=revert_alter_unique)
    ]

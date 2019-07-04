# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

from lms.djangoapps.onboarding.helpers import convert_date_to_utcdatetime, its_been_year


def oef_exists(org):
    """
    :param org:
    :return: True if some oef exists against this organization, otherwise False
    """
    return org.organization_oef_scores.count() > 0


def get_latest_oef(org):
    """
    :param org:
    :return: return latest oef score record
    """
    return org.organization_oef_scores.order_by('-finish_date').first()


def get_latest_finish_date(org):
    """
    :param org:
    :return: return finish date of latest oef record
    """
    return get_latest_oef(org).finish_date


def get_responsible_user(org):
    """
    :param org:
    :return: organization's admin or the user who submitted latest oef record
    """
    return org.admin if org.admin else get_latest_oef(org).user


def create_org_oef_prompts(apps, schema_editor):
    Organization = apps.get_model("onboarding", "Organization")
    OefPrompt = apps.get_model("oef", "OrganizationOefUpdatePrompt")

    # raw query is just for performance optimization. We pick only those organizations which have so
    organizations = Organization.objects.raw(
        """
        SELECT  `onboarding_organization`.*
        FROM `onboarding_organization` 
        INNER JOIN `oef_organizationoefscore` 
        ON (`onboarding_organization`.`id` = `oef_organizationoefscore`.`org_id`)
        WHERE `oef_organizationoefscore`.`finish_date` IS NOT NULL
        group by `onboarding_organization`.`id`
        """
    )

    OefPrompt.objects.all().delete()
    for org in organizations:
        if oef_exists(org):
            prompt = OefPrompt()
            finish_date = get_latest_finish_date(org)

            prompt.org = org
            prompt.responsible_user = get_responsible_user(org)
            prompt.latest_finish_date = finish_date
            prompt.year = its_been_year(convert_date_to_utcdatetime(finish_date))
            prompt.save()

class Migration(migrations.Migration):

    dependencies = [
        ('oef', '0012_organizationoefupdateprompt'),
    ]

    operations = [
        migrations.RunPython(create_org_oef_prompts)
    ]

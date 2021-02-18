from django.db.models.signals import post_save
from django.dispatch import receiver

from oef.models import OrganizationOefScore, OrganizationOefUpdatePrompt
from lms.djangoapps.onboarding.helpers import convert_date_to_utcdatetime, its_been_year


@receiver(post_save, sender=OrganizationOefScore)
def update_oef_prompts(instance, **kwargs):
    oef_prompt = OrganizationOefUpdatePrompt.objects.filter(org_id=instance.org_id).first()

    # Prepare date for prompt against this save in Organization Metric
    finish_date = instance.finish_date

    # oef is not yet completed
    if not finish_date:
        return

    responsible_user = instance.org.admin or instance.user
    org = instance.org

    latest_finish_date = convert_date_to_utcdatetime(finish_date)
    year = its_been_year(latest_finish_date)

    # If prompts against this Oef already exists, update that prompt
    if oef_prompt:
        oef_prompt.responsible_user = responsible_user
        oef_prompt.latest_finish_date = finish_date
        oef_prompt.year = year
        oef_prompt.save()
    else:
        # ceate a new prompt and save it
        prompt = OrganizationOefUpdatePrompt(
            responsible_user=responsible_user,
            org=org,
            latest_finish_date=finish_date,
            year=year
        )
        prompt.save()

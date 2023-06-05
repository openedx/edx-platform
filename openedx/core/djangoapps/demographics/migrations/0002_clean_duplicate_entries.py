import logging

from django.conf import settings
from django.db import migrations, models

log = logging.getLogger(__name__)


def _clean_duplicate_entries(apps, schema_editor):
    """
    This method finds all the duplicate user entries in the UserDemographics model
    and then removes all duplicate entries except for the most recently modified one.
    """
    demographics_model = apps.get_model('demographics', 'UserDemographics')
    # Retrieve a list of all users that have more than one entry.
    duplicate_users = (
        demographics_model.objects.values(
            'user'
        ).annotate(models.Count('id')).values('user').order_by().filter(id__count__gt=1)
    )
    # Get a QuerySet of all the UserDemographics instances for the duplicates
    # sorted by user and modified in descending order.
    user_demographic_dupes = demographics_model.objects.filter(user__in=duplicate_users).order_by('user', '-modified')

    # Go through the QuerySet and only keep the most recent instance.
    existing_user_ids = set()
    for demographic in user_demographic_dupes:
        if demographic.user_id in existing_user_ids:
            log.info('UserDemographics {user} -- {modified}'.format(
                user=demographic.user_id, modified=demographic.modified
            ))
            demographic.delete()
        else:
            log.info('UserDemographics Duplicate User Delete {user} -- {modified}'.format(
                user=demographic.user_id, modified=demographic.modified
            ))
            existing_user_ids.add(demographic.user_id)


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('demographics', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(_clean_duplicate_entries, migrations.RunPython.noop),
    ]

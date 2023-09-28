from django.db import migrations

from ..models import save_siteconfig_without_historical_record


def copy_column_values(apps, schema_editor):
    """
    Copy the contents of the values field into the site_values field in both
    SiteConfiguration and SiteConfigurationHistory.
    """
    # Update all values in the model.
    SiteConfiguration = apps.get_model('site_configuration', 'SiteConfiguration')
    for site_configuration in SiteConfiguration.objects.all():
        site_configuration.site_values = site_configuration.values
        # It would be incorrect to record these saves in the history table since it is
        # just backfilling data.  Use save_without_historical_record() instead of
        # save().
        save_siteconfig_without_historical_record(site_configuration)

    # Update all values in the history model.
    SiteConfigurationHistory = apps.get_model('site_configuration', 'SiteConfigurationHistory')
    for historical_site_configuration in SiteConfigurationHistory.objects.all():
        historical_site_configuration.site_values = historical_site_configuration.values
        historical_site_configuration.save()


class Migration(migrations.Migration):

    dependencies = [
        ('site_configuration', '0005_populate_siteconfig_history_site_values'),
    ]

    operations = [
        migrations.RunPython(
            copy_column_values,
            reverse_code=migrations.RunPython.noop,  # Allow reverse migrations, but make it a no-op.
        ),
    ]

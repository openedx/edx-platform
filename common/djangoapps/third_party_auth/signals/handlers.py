"""
Signal handlers for third_party_auth app.
"""

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from ..models import SAMLConfiguration, SAMLProviderConfig

log = logging.getLogger(__name__)


@receiver(post_save, sender=SAMLConfiguration)
def update_saml_provider_configs_on_configuration_change(sender, instance, created, **kwargs):
    """
    Signal handler to update SAMLProviderConfig instances when SAMLConfiguration is updated.
    """
    try:
        provider_configs = SAMLProviderConfig.objects.current_set().filter(
            site_id=instance.site_id,
            saml_configuration__slug=instance.slug
        ).exclude(saml_configuration_id=instance.id)

        updated_count = 0
        for provider_config in provider_configs:
            if not provider_config.saml_configuration.enabled:
                provider_config.saml_configuration = instance
                provider_config.save()
                updated_count += 1

        if updated_count > 0:
            log.info("Updated %d SAMLProviderConfig instances", updated_count)

    except Exception as e:  # pylint: disable=broad-except
        log.warning("Error in SAMLConfiguration signal: %s", e)

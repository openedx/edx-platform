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

    When a SAMLConfiguration is updated, ConfigurationModel creates a new version.
    This handler ensures that all EXISTING SAMLProviderConfig instances that were using
    the old configuration are updated to point to the new version - NO new providers are created.
    """
    try:
        # Find all EXISTING SAMLProviderConfig instances (current_set) that should be
        # pointing to this slug but are pointing to an older version
        existing_providers = SAMLProviderConfig.objects.current_set().filter(
            site_id=instance.site_id,
            saml_configuration__slug=instance.slug
        ).exclude(saml_configuration_id=instance.id)

        updated_count = 0
        for provider_config in existing_providers:
            # Update the EXISTING provider to point to the new parent configuration
            old_config_id = provider_config.saml_configuration_id
            
            # Use update() instead of save() to avoid creating new ConfigurationModel records
            SAMLProviderConfig.objects.filter(id=provider_config.id).update(
                saml_configuration_id=instance.id
            )

            log.info(
                "Updated EXISTING SAMLProviderConfig '%s' from old parent ID %s to new parent ID %s",
                provider_config.slug,
                old_config_id,
                instance.id
            )
            updated_count += 1

        if updated_count > 0:
            log.info("Updated %d existing SAMLProviderConfig instances to point to new parent", updated_count)

    except Exception as e:  # pylint: disable=broad-except
        log.warning("Error in SAMLConfiguration post_save signal: %s", e)

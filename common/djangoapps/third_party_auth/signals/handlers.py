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
    This handler ensures that all SAMLProviderConfig instances that were using
    the old configuration are updated to point to the new version.
    """
    if not instance.enabled:
        return
    
    try:
        current_config = SAMLConfiguration.current(instance.site_id, instance.slug)
        # Only proceed if this instance is actually the current one
        if not current_config or current_config.id != instance.id:
            return
            
        # Find all SAMLProviderConfig instances that reference any version of this configuration
        provider_configs = SAMLProviderConfig.objects.current_set().filter(
            site_id=instance.site_id,
            saml_configuration__slug=instance.slug
        ).exclude(saml_configuration_id=instance.id)
        
        updated_count = 0
        for provider_config in provider_configs:
            log.info(
                "Updating SAMLProviderConfig '%s' to use new SAMLConfiguration version (ID: %s -> %s)",
                provider_config.slug,
                provider_config.saml_configuration_id,
                instance.id
            )
            provider_config.saml_configuration = instance
            provider_config.save()
            updated_count += 1
        
        if updated_count > 0:
            log.info("Updated %d SAMLProviderConfig instances to use new SAMLConfiguration version", updated_count)
            
    except Exception as e:
        log.warning("Error in SAMLConfiguration post_save signal: %s", e)
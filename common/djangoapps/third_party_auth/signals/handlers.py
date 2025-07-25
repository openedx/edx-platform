"""
Signal handlers for third_party_auth app.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from edx_django_utils.monitoring import set_custom_attribute

from ..models import SAMLConfiguration, SAMLProviderConfig, ENABLE_SAML_CONFIG_SIGNAL_HANDLERS


@receiver(post_save, sender=SAMLConfiguration)
def update_saml_provider_configs_on_configuration_change(sender, instance, created, **kwargs):
    """
    Signal handler to update SAMLProviderConfig instances when SAMLConfiguration is updated.

    When a SAMLConfiguration is updated, ConfigurationModel creates a new version.
    This handler ensures that all EXISTING SAMLProviderConfig instances that were using
    the old configuration are updated to point to the new version - NO new providers are created.

    This behavior is controlled by the ENABLE_SAML_CONFIG_SIGNAL_HANDLERS toggle.
    When disabled, this handler does nothing (legacy behavior).

    """
    # .. custom_attribute_name: saml_config_signal.enabled
    # .. custom_attribute_description: Tracks whether the SAML config signal handler is enabled.
    set_custom_attribute('saml_config_signal.enabled', ENABLE_SAML_CONFIG_SIGNAL_HANDLERS.is_enabled())

    # .. custom_attribute_name: saml_config_signal.new_config_id
    # .. custom_attribute_description: Records the ID of the new SAML configuration instance.
    set_custom_attribute('saml_config_signal.new_config_id', instance.id)

    # .. custom_attribute_name: saml_config_signal.slug
    # .. custom_attribute_description: Records the slug of the SAML configuration instance.
    set_custom_attribute('saml_config_signal.slug', instance.slug)

    if ENABLE_SAML_CONFIG_SIGNAL_HANDLERS.is_enabled():
        try:
            # Find all EXISTING SAMLProviderConfig instances (current_set) that should be
            # pointing to this slug but are pointing to an older version
            existing_providers = SAMLProviderConfig.objects.current_set().filter(
                site_id=instance.site_id,
                saml_configuration__slug=instance.slug
            ).exclude(saml_configuration_id=instance.id)

            updated_count = 0
            for provider_config in existing_providers:
                # Create a new versioned SAMLProviderConfig record by saving with the new saml_configuration
                old_config_id = provider_config.saml_configuration_id
                provider_config.saml_configuration = instance
                provider_config.save()
                updated_count += 1

            # .. custom_attribute_name: saml_config_signal.updated_count
            # .. custom_attribute_description: The number of SAMLProviderConfig records updated to point to the new configuration.
            set_custom_attribute('saml_config_signal.updated_count', updated_count)

            # Use simple, atomic custom attributes for observability
            set_custom_attribute('saml_config.signal_behavior.enabled', True)
            set_custom_attribute('saml_config.signal_behavior.config_id', instance.id)
            set_custom_attribute('saml_config.signal_behavior.slug', instance.slug)
            set_custom_attribute('saml_config.signal_behavior.updated_count', updated_count)

        except Exception as e:  # pylint: disable=broad-except

            error_type = type(e).__name__
            set_custom_attribute('saml_config_signal.error_type', error_type)
            set_custom_attribute('saml_config_signal.error_message', str(e))

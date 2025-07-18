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

    Observability is provided regardless of toggle state.
    """
    # Check if the toggle is enabled and execute accordingly
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
                # Update the EXISTING provider to point to the new parent configuration
                old_config_id = provider_config.saml_configuration_id

                # Use update() instead of save() to avoid creating new ConfigurationModel records
                SAMLProviderConfig.objects.filter(id=provider_config.id).update(
                    saml_configuration_id=instance.id
                )

                # .. custom_attribute_name: saml_config.signal_update
                # .. custom_attribute_description: Tracks when signal handler updates SAML provider
                #     config references to point to latest configuration version.
                set_custom_attribute(
                    'saml_config.signal_update',
                    'updated_reference:provider_id=' + str(provider_config.id) + ',' +
                    'old_config_id=' + str(old_config_id) + ',new_config_id=' + str(instance.id)
                )

                updated_count += 1

            # Always record final behavior regardless of updates
            if updated_count > 0:
                set_custom_attribute(
                    'saml_config.signal_behavior',
                    'active:config_id=' + str(instance.id) + ',updated_count=' + str(updated_count)
                )
            else:
                set_custom_attribute(
                    'saml_config.signal_behavior',
                    'active_no_updates:config_id=' + str(instance.id)
                )

        except Exception as e:  # pylint: disable=broad-except
            # Always record errors for observability
            error_type = type(e).__name__
            set_custom_attribute('saml_config.signal_behavior', 'error:config_id=' + str(instance.id))
            set_custom_attribute('saml_config.signal_error', error_type + ':' + str(e))
    else:
        # .. custom_attribute_name: saml_config.signal_behavior
        # .. custom_attribute_description: Tracks whether signal handler is active or disabled by toggle.
        #    When disabled, includes details about the legacy behavior and which config was ignored.
        set_custom_attribute(
            'saml_config.signal_behavior',
            'disabled_by_toggle:slug=' + instance.slug + ',config_id=' + str(instance.id)
        )

"""
Django models for site configurations.
"""

import beeline

import collections
from logging import getLogger
from sass import CompileError

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.files.storage import get_storage_class
from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils.encoding import python_2_unicode_compatible
from jsonfield.fields import JSONField
from model_utils.models import TimeStampedModel

from ..appsembler.preview.helpers import is_preview_mode


logger = getLogger(__name__)  # pylint: disable=invalid-name


def get_initial_sass_variables():
    """
    Proxy to `utils.get_initial_sass_variables` to avoid test-time Django errors.

    # TODO: Fix Site Configuration and Organizations hacks. https://github.com/appsembler/edx-platform/issues/329
    """
    from openedx.core.djangoapps.appsembler.sites import utils
    return utils.get_initial_sass_variables()


def get_initial_page_elements():
    """
    Proxy to `utils.get_initial_page_elements` to avoid test-time Django errors.

    # TODO: Fix Site Configuration and Organizations hacks. https://github.com/appsembler/edx-platform/issues/329
    """
    from openedx.core.djangoapps.appsembler.sites import utils
    return utils.get_initial_page_elements()


def get_customer_themes_storage():
    storage_class = get_storage_class(settings.DEFAULT_FILE_STORAGE)
    return storage_class(**settings.CUSTOMER_THEMES_BACKEND_OPTIONS)


THEME_AMC_V1 = 'amc-v1'
THEME_TAHOE_V2 = 'tahoe-v2'


@python_2_unicode_compatible
class SiteConfiguration(models.Model):
    """
    Model for storing site configuration. These configuration override OpenEdx configurations and settings.
    e.g. You can override site name, logo image, favicon etc. using site configuration.

    Fields:
        site (OneToOneField): one to one field relating each configuration to a single site
        site_values (JSONField):  json field to store configurations for a site

    .. no_pii:
    """

    api_adapter = None  # Tahoe: Placeholder for `site_config_client`'s `SiteConfigAdapter`
    tahoe_config_modifier = None  # Tahoe: Placeholder for `TahoeConfigurationValueModifier` instance

    site = models.OneToOneField(Site, related_name='configuration', on_delete=models.CASCADE)
    enabled = models.BooleanField(default=False, verbose_name=u"Enabled")
    site_values = JSONField(
        null=False,
        blank=True,
        # The actual default value is determined by calling the given callable.
        # Therefore, the default here is just {}, since that is the result of
        # calling `dict`.
        default=dict,
        load_kwargs={'object_pairs_hook': collections.OrderedDict}
    )
    sass_variables = JSONField(blank=True, default=get_initial_sass_variables)
    page_elements = JSONField(blank=True, default=get_initial_page_elements)

    def __str__(self):
        return u"<SiteConfiguration: {site} >".format(site=self.site)  # xss-lint: disable=python-wrap-html

    def __repr__(self):
        return self.__str__()

    @beeline.traced('site_config.init_api_client_adapter')
    def init_api_client_adapter(self, site):
        """
        Initialize `api_adapter`, this method is managed externally by `get_current_site_configuration()`.
        """
        # Tahoe: Import is placed here to avoid model import at project startup
        from openedx.core.djangoapps.appsembler.sites import (
            site_config_client_helpers as site_helpers,
        )
        if site_helpers.is_enabled_for_site(site):
            self.api_adapter = site_helpers.init_site_configuration_adapter(site)

    @beeline.traced('site_config.get_value')
    def get_value(self, name, default=None):
        """
        Return Configuration value for the key specified as name argument.

        Function logs a message if configuration is not enabled or if there is an error retrieving a key.

        Args:
            name (str): Name of the key for which to return configuration value.
            default: default value tp return if key is not found in the configuration

        Returns:
            Configuration value for the given key or returns `None` if configuration is not enabled.
        """
        beeline.add_context_field('value_name', name)
        if self.enabled:
            if self.tahoe_config_modifier:
                name, default = self.tahoe_config_modifier.normalize_get_value_params(name, default)
                should_override, overridden_value = self.tahoe_config_modifier.override_value(name)
                if should_override:
                    return overridden_value

            try:
                if self.api_adapter:
                    # Tahoe: Use `SiteConfigAdapter` if available.
                    beeline.add_context_field('value_source', 'site_config_service')
                    return self.api_adapter.get_value_of_type(self.api_adapter.TYPE_SETTING, name, default)
                else:
                    beeline.add_context_field('value_source', 'django_model')
                    return self.site_values.get(name, default) if self.site_values else default
            except AttributeError as error:
                logger.exception(u'Invalid JSON data. \n [%s]', error)
        else:
            logger.info(u"Site Configuration is not enabled for site (%s).", self.site)

        return default

    @beeline.traced('site_config.get_page_content')
    def get_page_content(self, name, default=None):
        """
        Tahoe: Get page content from Site Configuration service settings.

        If SiteConfiguration adapter isn't in use, fallback to the deprecated `SiteConfiguration.page_elements` field.

        Args:
            name (str): Name of the page to fetch.
            default: default value to return if page is not found in the configuration.

        Returns:
            Page content `dict`.
        """
        if self.api_adapter:
            # Tahoe: Use `SiteConfigAdapter` if available.
            beeline.add_context_field('page_source', 'site_config_service')
            return self.api_adapter.get_value_of_type(self.api_adapter.TYPE_PAGE, name, default)
        else:
            beeline.add_context_field('page_source', 'django_model')
            return self.page_elements.get(name, default)

    @beeline.traced('site_config.get_admin_setting')
    def get_admin_setting(self, name, default=None):
        """
        Tahoe: Get `admin` setting from the site configuration service.

        If SiteConfiguration adapter isn't in use, fallback to the deprecated `SiteConfiguration.site_values` field.

        Args:
            name (str): Name of the setting to fetch.
            default: default value to return if setting is not found in the configuration.

        Returns:
            Value for the given key or returns `None` if not configured.
        """
        if self.api_adapter:
            # Tahoe: Use `SiteConfigAdapter` if available.
            beeline.add_context_field('setting_source', 'site_config_service')
            return self.api_adapter.get_value_of_type(self.api_adapter.TYPE_ADMIN, name, default)
        else:
            beeline.add_context_field('setting_source', 'django_model')
            return self.site_values.get(name, default) if self.site_values else default

    @beeline.traced('site_config.get_secret_value')
    def get_secret_value(self, name, default=None):
        """
        Tahoe: Get `secret` value from the site configuration service.

        If SiteConfiguration adapter isn't in use, fallback to the deprecated `SiteConfiguration.site_values` field.

        Args:
            name (str): Name of the secret to fetch.
            default: default value to return if secret is not found in the configuration.

        Returns:
            Value for the given key or returns `None` if not configured.
        """
        if self.api_adapter:
            # Tahoe: Use `SiteConfigAdapter` if available.
            beeline.add_context_field('setting_source', 'site_config_service')
            return self.api_adapter.get_value_of_type(self.api_adapter.TYPE_SECRET, name, default)
        else:
            beeline.add_context_field('setting_source', 'django_model')
            return self.site_values.get(name, default) if self.site_values else default

    @classmethod
    def get_configuration_for_org(cls, org, select_related=None):
        """
        This returns a SiteConfiguration object which has an org_filter that matches
        the supplied org

        Args:
            org (str): Org to use to filter SiteConfigurations
            select_related (list or None): A list of values to pass as arguments to select_related
        """
        query = cls.objects.filter(site_values__contains=org, enabled=True)

        if hasattr(SiteConfiguration, 'sass_variables'):
            # TODO: Clean up Site Configuration hacks: https://github.com/appsembler/edx-platform/issues/329
            query = query.defer('page_elements', 'sass_variables')

        if select_related is not None:
            query = query.select_related(*select_related)
        for configuration in query:
            course_org_filter = configuration.get_value('course_org_filter', [])
            # The value of 'course_org_filter' can be configured as a string representing
            # a single organization or a list of strings representing multiple organizations.
            if not isinstance(course_org_filter, list):
                course_org_filter = [course_org_filter]
            if org in course_org_filter:
                return configuration
        return None

    @classmethod
    def get_value_for_org(cls, org, name, default=None):
        """
        This returns site configuration value which has an org_filter that matches
        what is passed in,

        Args:
            org (str): Course ord filter, this value will be used to filter out the correct site configuration.
            name (str): Name of the key for which to return configuration value.
            default: default value tp return if key is not found in the configuration

        Returns:
            Configuration value for the given key.
        """
        configuration = cls.get_configuration_for_org(org)
        if configuration is None:
            return default
        else:
            return configuration.get_value(name, default)

    @classmethod
    def get_all_orgs(cls):
        """
        This returns all of the orgs that are considered in site configurations, This can be used,
        for example, to do filtering.

        Returns:
            A set of all organizations present in site configuration.
        """
        org_filter_set = set()

        query = cls.objects.filter(site_values__contains='course_org_filter', enabled=True)
        if hasattr(SiteConfiguration, 'sass_variables'):
            # TODO: Clean up Site Configuration hacks: https://github.com/appsembler/edx-platform/issues/329
            query = query.defer('page_elements', 'sass_variables')

        for configuration in query:
            course_org_filter = configuration.get_value('course_org_filter', [])
            if not isinstance(course_org_filter, list):
                course_org_filter = [course_org_filter]
            org_filter_set.update(course_org_filter)
        return org_filter_set

    @classmethod
    def has_org(cls, org):
        """
        Check if the given organization is present in any of the site configuration.

        Returns:
            True if given organization is present in site configurations otherwise False.
        """
        return org in cls.get_all_orgs()

    def delete(self, using=None):
        self.delete_css_override()
        super(SiteConfiguration, self).delete(using=using)

    def get_css_overrides_file(self, preview=None):
        """
        Return the css override file base name.

        Depending on the `preview` parameter, the file can be returned either for preview (`draft`) or live CSS file.
        """
        domain = self.site.domain
        domain_without_port_number = domain.split(':')[0]

        if preview is None:
            preview = is_preview_mode()

        if preview:
            css_file_prefix = 'preview-'
        else:
            css_file_prefix = ''
        return '{prefix}{domain}.css'.format(
            prefix=css_file_prefix,
            domain=domain_without_port_number,
        )

    def get_theme_version(self):
        return self.get_value('THEME_VERSION', THEME_AMC_V1)

    def compile_microsite_sass(self):
        """
        Compiles the microsite sass and save it into the storage bucket.

        :return dict {
          "successful_sass_compile": boolean: whether the CSS was compiled successfully
          "sass_compile_message": string: Status message that's safe to show for customers.
          "scss_file_used": string: The source css file name.
          "site_css_file": string: The stored file in the customer theme storage.
          "theme_version": string: Theme version.
          "configuration_source": string: "site_config_service_client" or "openedx_site_configuration_model".
        }
        """
        # Importing `sites.utils` locally to avoid test-time Django errors.
        # TODO: Fix Site Configuration and Organizations hacks. https://github.com/appsembler/edx-platform/issues/329
        from openedx.core.djangoapps.appsembler.sites import utils as sites_utils

        if self.api_adapter:
            configuration_source = 'site_config_service_client'
            # Clear cache to fetch fresh css and config variables
            self.api_adapter.delete_backend_configs_cache()
        else:
            configuration_source = 'openedx_site_configuration_model'

        storage = get_customer_themes_storage()
        css_file_name = self.get_css_overrides_file()
        theme_version = self.get_theme_version()
        if theme_version == THEME_TAHOE_V2:
            scss_file = '_main-v2.scss'
        else:
            # TODO: Deprecated. Remove once all sites are migrated to Tahoe 2.0 structure.
            scss_file = 'main.scss'

        try:
            css_output = sites_utils.compile_sass(scss_file, custom_branding=self._sass_var_override)
            with storage.open(css_file_name, 'w') as f:
                f.write(css_output)
            successful_sass_compile = True
            sass_compile_message = 'Sass compile finished successfully for site {site}'.format(site=self.site.domain)
        except CompileError as exc:
            successful_sass_compile = False
            sass_compile_message = 'Sass compile failed for site {site} with the error: {message}'.format(
                site=self.site.domain,
                message=str(exc),
            )
            logger.warning(sass_compile_message, exc_info=True)

        return {
            'successful_sass_compile': successful_sass_compile,
            'sass_compile_message': sass_compile_message,
            'scss_file_used': scss_file,
            'site_css_file': css_file_name,
            'theme_version': theme_version,
            'configuration_source': configuration_source,
        }

    def get_css_url(self, preview=None):
        """
        Return the fully qualified css override file with to be included in the theme.

        Depending on the `preview` parameter, the file can be returned either for preview (`draft`) or live CSS file.

        If the preview css file isn't compiled, the live CSS file will be returned.
        """
        storage = get_customer_themes_storage()

        if preview is None:
            preview = is_preview_mode()

        css_override_file = self.get_css_overrides_file(preview=preview)

        if preview and not storage.exists(css_override_file):
            # If the CSS preview file is stale or missing use the regular one
            css_override_file = self.get_css_overrides_file(preview=False)

        return storage.url(css_override_file)

    def set_sass_variables(self, entries):
        """
        Accepts a dict with the shape { var_name: value } and sets the SASS variables
        """
        for index, entry in enumerate(self.sass_variables):
            var_name = entry[0]
            if var_name in entries:
                new_value = (var_name, [entries[var_name], entries[var_name]])
                self.sass_variables[index] = new_value

    def delete_css_override(self):
        live_css_file = self.get_css_overrides_file()
        draft_css_file = self.get_css_overrides_file()

        for css_file in [live_css_file, draft_css_file]:
            try:
                storage = get_customer_themes_storage()
                storage.delete(css_file)
            except Exception:  # pylint: disable=broad-except  # noqa
                logger.warning("Can't delete CSS file {}".format(css_file))

    @beeline.traced('site_config._get_theme_v1_variables_overrides')
    def _get_theme_v1_variables_overrides(self):
        """
        Get the amc-v1 theme variable overrides.

        TODO: Remove once AMC is shut down.
        """
        beeline.add_context_field('value_source', 'django_model')
        sass_variables = self.sass_variables
        return " ".join(["{}: {};".format(var, val[0]) for var, val in sass_variables])

    @beeline.traced('site_config._get_theme_v2_variables_overrides')
    def _get_theme_v2_variables_overrides(self):
        """
        Get tahoe-v2 variable names.
        """
        beeline.add_context_field('value_source', 'site_config_service')

        if self.api_adapter:
            # Tahoe: Use `SiteConfigAdapter` if available.
            beeline.add_context_field('value_source', 'site_config_service')
            css_variables_dict = self.api_adapter.get_css_variables_dict()
        else:
            beeline.add_context_field('value_source', 'django_model')
            # Assume a sass variables dict, this is useful for devstack and testing purposes.
            css_variables_dict = self.sass_variables

        if not isinstance(css_variables_dict, dict):
            raise Exception('_get_theme_v2_variables_overrides expects a theme v2 dictionary of css variables')

        return " ".join(["${}: {};".format(var, val) for var, val in css_variables_dict.items()])

    def _sass_var_override(self, path):
        if 'branding-basics' in path:
            # TODO: Remove once AMC is shut down.
            return [(path, self._get_theme_v1_variables_overrides())]
        if 'tahoe-v2-variables-overrides' in path:
            return [(path, self._get_theme_v2_variables_overrides())]
        if 'customer-sass-input' in path:
            return [(path, self.get_value('customer_sass_input', ''))]
        return None


@receiver(post_save, sender=SiteConfiguration)
def compile_tahoe_microsite_sass_on_site_config_save(sender, instance, created, **kwargs):
    """
    Tahoe: Compile Tahoe microsite scss on saving the SiteConfiguration model.

    This signal receiver maintains backward compatibility with existing sites and the Appsembler Management
    Console (AMC).

    # TODO: RED-2847 - Remove this signal receiver after all Tahoe sites switch to Dashboard.
    """
    sass_status = instance.compile_microsite_sass()
    if sass_status['successful_sass_compile']:
        logger.info('tahoe sass compiled successfully: %s', sass_status['sass_compile_message'])
    else:
        logger.warning('tahoe css compile error: %s', sass_status['sass_compile_message'])


def save_siteconfig_without_historical_record(siteconfig, *args, **kwargs):
    """
    Save model without saving a historical record

    Make sure you know what you're doing before you use this method.

    Note: this method is copied verbatim from django-simple-history.
    """
    siteconfig.skip_history_when_saving = True
    try:
        ret = siteconfig.save(*args, **kwargs)
    finally:
        del siteconfig.skip_history_when_saving
    return ret


@python_2_unicode_compatible
class SiteConfigurationHistory(TimeStampedModel):
    """
    This is an archive table for SiteConfiguration, so that we can maintain a history of
    changes. Note that the site field is not unique in this model, compared to SiteConfiguration.

    Fields:
        site (ForeignKey): foreign-key to django Site
        site_values (JSONField): json field to store configurations for a site

    .. no_pii:
    """
    site = models.ForeignKey(Site, related_name='configuration_histories', on_delete=models.CASCADE)
    enabled = models.BooleanField(default=False, verbose_name=u"Enabled")
    site_values = JSONField(
        null=False,
        blank=True,
        load_kwargs={'object_pairs_hook': collections.OrderedDict}
    )

    class Meta:
        get_latest_by = 'modified'
        ordering = ('-modified', '-created',)

    def __str__(self):
        # pylint: disable=line-too-long
        return u"<SiteConfigurationHistory: {site}, Last Modified: {modified} >".format(  # xss-lint: disable=python-wrap-html
            modified=self.modified,
            site=self.site,
        )

    def __repr__(self):
        return self.__str__()


@receiver(post_save, sender=SiteConfiguration)
def update_site_configuration_history(sender, instance, created, **kwargs):  # pylint: disable=unused-argument
    """
    Add site configuration changes to site configuration history.

    Recording history on updates and deletes can be skipped by first setting
    the `skip_history_when_saving` attribute on the instace, e.g.:

      site_config.skip_history_when_saving = True
      site_config.save()

    Args:
        sender: sender of the signal i.e. SiteConfiguration model
        instance: SiteConfiguration instance associated with the current signal
        created (bool): True if a new record was created.
        **kwargs: extra key word arguments
    """
    # Skip writing history when asked by the caller.  This skip feature only
    # works for non-creates.
    if created or not hasattr(instance, "skip_history_when_saving"):
        SiteConfigurationHistory.objects.create(
            site=instance.site,
            site_values=instance.site_values,
            enabled=instance.enabled,
        )

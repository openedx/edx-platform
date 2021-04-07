"""
Django models for site configurations.
"""


import collections
from logging import getLogger
import os
from urllib.parse import urlsplit

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.files.storage import get_storage_class
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.encoding import python_2_unicode_compatible
from jsonfield.fields import JSONField
from model_utils.models import TimeStampedModel

from .exceptions import TahoeConfigurationException

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

    def save(self, **kwargs):
        # When creating a new object, save default microsite values. Not implemented as a default method on the field
        # because it depends on other fields that should be already filled.
        self.site_values = self.site_values or {}
        if not self.site_values.get('PLATFORM_NAME'):
            # Initialize the values for new SiteConfiguration objects
            self.site_values.update(self.get_initial_microsite_values())

        # fix for a bug with some pages requiring uppercase platform_name variable
        self.site_values['PLATFORM_NAME'] = self.site_values.get('platform_name', '')

        # Set the default language code for new sites if missing
        # TODO: Move it to somewhere else like in AMC
        self.site_values['LANGUAGE_CODE'] = self.site_values.get('LANGUAGE_CODE', 'en')

        # We cannot simply use a protocol-relative URL for LMS_ROOT_URL
        # This is because the URL here will be used by such activities as
        # sending activation links to new users. The activation link needs the
        # scheme address verfication emails. The callers using this variable
        # expect the scheme in the URL
        self.site_values['LMS_ROOT_URL'] = '{scheme}://{domain}'.format(
            scheme=urlsplit(settings.LMS_ROOT_URL).scheme,
            domain=self.site.domain)

        super(SiteConfiguration, self).save(**kwargs)

        # recompile SASS on every save
        self.compile_microsite_sass()
        return self

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
        if self.enabled:
            try:
                return self.site_values.get(name, default)
            except AttributeError as error:
                logger.exception(u'Invalid JSON data. \n [%s]', error)
        else:
            logger.info(u"Site Configuration is not enabled for site (%s).", self.site)

        return default

    @classmethod
    def get_configuration_for_org(cls, org, select_related=None):
        """
        This returns a SiteConfiguration object which has an org_filter that matches
        the supplied org

        Args:
            org (str): Org to use to filter SiteConfigurations
            select_related (list or None): A list of values to pass as arguments to select_related
        """
        query = cls.objects.filter(site_values__contains=org, enabled=True).defer('page_elements', 'sass_variables').all()
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

        for configuration in cls.objects.filter(site_values__contains='course_org_filter', enabled=True).defer('page_elements', 'sass_variables').all():
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

    def compile_microsite_sass(self):
        # Importing `compile_sass` to avoid test-time Django errors.
        # TODO: Fix Site Configuration and Organizations hacks. https://github.com/appsembler/edx-platform/issues/329
        from openedx.core.djangoapps.appsembler.sites.utils import compile_sass
        css_output = compile_sass('main.scss', custom_branding=self._sass_var_override)
        file_name = self.get_value('css_overrides_file')

        if not file_name:
            if settings.TAHOE_SILENT_MISSING_CSS_CONFIG:
                return  # Silent the exception below on during testing
            else:
                raise TahoeConfigurationException(
                    'Missing `css_overrides_file` from SiteConfiguration for `{site}` config_id=`{id}`'.format(
                        site=self.site.domain,
                        id=self.id,
                    )
                )

        storage = self.get_customer_themes_storage()
        with storage.open(file_name, 'w') as f:
            f.write(css_output)

    def get_css_url(self):
        storage = self.get_customer_themes_storage()
        return storage.url(self.get_value('css_overrides_file'))

    def set_sass_variables(self, entries):
        """
        Accepts a dict with the shape { var_name: value } and sets the SASS variables
        """
        for index, entry in enumerate(self.sass_variables):
            var_name = entry[0]
            if var_name in entries:
                new_value = (var_name, [entries[var_name], entries[var_name]])
                self.sass_variables[index] = new_value

    def get_customer_themes_storage(self):
        storage_class = get_storage_class(settings.DEFAULT_FILE_STORAGE)
        return storage_class(**settings.CUSTOMER_THEMES_BACKEND_OPTIONS)

    def delete_css_override(self):
        css_file = self.get_value('css_overrides_file')
        if css_file:
            try:
                storage = self.get_customer_themes_storage()
                storage.delete(self.get_value('css_overrides_file'))
            except Exception:  # pylint: disable=broad-except  # noqa
                logger.warning("Can't delete CSS file {}".format(css_file))

    def _formatted_sass_variables(self):
        return " ".join(["{}: {};".format(var, val[0]) for var, val in self.sass_variables])

    def _sass_var_override(self, path):
        if 'branding-basics' in path:
            return [(path, self._formatted_sass_variables())]
        if 'customer-sass-input' in path:
            return [(path, self.get_value('customer_sass_input', ''))]
        return None

    def get_initial_microsite_values(self):
        domain_without_port_number = self.site.domain.split(':')[0]
        return {
            'platform_name': self.site.name,
            'css_overrides_file': "{}.css".format(domain_without_port_number),
            'ENABLE_COMBINED_LOGIN_REGISTRATION': True,
        }


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

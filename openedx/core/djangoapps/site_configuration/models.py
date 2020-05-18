"""
Django models for site configurations.
"""
import collections
from logging import getLogger
import os

from django.conf import settings
from django.core.files.storage import get_storage_class
from django.contrib.sites.models import Site
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.core.files.storage import get_storage_class
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from jsonfield.fields import JSONField
from model_utils.models import TimeStampedModel


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


class SiteConfiguration(models.Model):
    """
    Model for storing site configuration. These configuration override OpenEdx configurations and settings.
    e.g. You can override site name, logo image, favicon etc. using site configuration.

    Fields:
        site (OneToOneField): one to one field relating each configuration to a single site
        values (JSONField):  json field to store configurations for a site
    """
    site = models.OneToOneField(Site, related_name='configuration', on_delete=models.CASCADE)
    enabled = models.BooleanField(default=False, verbose_name="Enabled")
    values = JSONField(
        null=False,
        blank=True,
        load_kwargs={'object_pairs_hook': collections.OrderedDict}
    )
    sass_variables = JSONField(blank=True, default=get_initial_sass_variables)
    page_elements = JSONField(blank=True, default=get_initial_page_elements)

    def __unicode__(self):
        return u"<SiteConfiguration: {site} >".format(site=self.site)

    def __repr__(self):
        return self.__unicode__()

    def save(self, **kwargs):
        # When creating a new object, save default microsite values. Not implemented as a default method on the field
        # because it depends on other fields that should be already filled.
        if not self.id:
            self.values = self.get_initial_microsite_values()

        # fix for a bug with some pages requiring uppercase platform_name variable
        self.values['PLATFORM_NAME'] = self.values.get('platform_name', '')

        # Set the default language code for new sites if missing
        # TODO: Move it to somewhere else like in AMC
        self.values['LANGUAGE_CODE'] = self.values.get('LANGUAGE_CODE', 'en')

        super(SiteConfiguration, self).save(**kwargs)

        # recompile SASS on every save
        self.compile_microsite_sass()
        #self.collect_css_file()
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
                return self.values.get(name, default)  # pylint: disable=no-member
            except AttributeError as error:
                logger.exception('Invalid JSON data. \n [%s]', error)
        else:
            logger.info("Site Configuration is not enabled for site (%s).", self.site)

        return default

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
        for configuration in cls.objects.filter(values__contains=org, enabled=True).defer('page_elements', 'sass_variables').all():
            course_org_filter = configuration.get_value('course_org_filter', [])
            # The value of 'course_org_filter' can be configured as a string representing
            # a single organization or a list of strings representing multiple organizations.
            if not isinstance(course_org_filter, list):
                course_org_filter = [course_org_filter]
            if org in course_org_filter:
                return configuration.get_value(name, default)
        return default

    @classmethod
    def get_all_orgs(cls):
        """
        This returns all of the orgs that are considered in site configurations, This can be used,
        for example, to do filtering.

        Returns:
            A list of all organizations present in site configuration.
        """
        org_filter_set = set()

        for configuration in cls.objects.filter(values__contains='course_org_filter', enabled=True).defer('page_elements', 'sass_variables').all():
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
        if settings.USE_S3_FOR_CUSTOMER_THEMES:
            storage_class = get_storage_class(settings.DEFAULT_FILE_STORAGE)
            storage = storage_class(
                location="customer_themes",
            )
            with storage.open(file_name, 'w') as f:
                f.write(css_output.encode('utf-8'))
        else:
            theme_folder = os.path.join(settings.COMPREHENSIVE_THEME_DIRS[0], 'customer_themes')
            theme_file = os.path.join(theme_folder, file_name)
            with open(theme_file, 'w') as f:
                f.write(css_output.encode('utf-8'))

    def get_css_url(self):
        if settings.USE_S3_FOR_CUSTOMER_THEMES:
            kwargs = {
                'location': "customer_themes",
            }
            storage = get_storage_class()(**kwargs)
            return storage.url(self.get_value('css_overrides_file'))
        else:
            return static("customer_themes/{}".format(self.get_value('css_overrides_file')))

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
        css_file = self.values.get('css_overrides_file')
        if css_file:
            try:
                if settings.USE_S3_FOR_CUSTOMER_THEMES:
                    kwargs = {
                        'location': "customer_themes",
                    }
                    storage = get_storage_class()(**kwargs)
                    storage.delete(self.get_value('css_overrides_file'))
                else:
                    os.remove(os.path.join(settings.COMPREHENSIVE_THEME_DIRS[0], css_file))
            except OSError:
                logger.warning("Can't delete CSS file {}".format(css_file))

    def _formatted_sass_variables(self):
        return " ".join(["{}: {};".format(var, val[0]) for var, val in self.sass_variables])

    def _sass_var_override(self, path):
        if 'branding-basics' in path:
            return [(path, self._formatted_sass_variables())]
        if 'customer-sass-input' in path:
            return [(path, self.values.get('customer_sass_input', ''))]
        return None

    def get_initial_microsite_values(self):
        domain_without_port_number = self.site.domain.split(':')[0]
        return {
            'platform_name': self.site.name,
            'css_overrides_file': "{}.css".format(domain_without_port_number),
            'ENABLE_COMBINED_LOGIN_REGISTRATION': True,
        }


class SiteConfigurationHistory(TimeStampedModel):
    """
    This is an archive table for SiteConfiguration, so that we can maintain a history of
    changes. Note that the site field is not unique in this model, compared to SiteConfiguration.

    Fields:
        site (ForeignKey): foreign-key to django Site
        values (JSONField): json field to store configurations for a site
    """
    site = models.ForeignKey(Site, related_name='configuration_histories', on_delete=models.CASCADE)
    enabled = models.BooleanField(default=False, verbose_name="Enabled")
    values = JSONField(
        null=False,
        blank=True,
        load_kwargs={'object_pairs_hook': collections.OrderedDict}
    )

    class Meta:
        get_latest_by = 'modified'
        ordering = ('-modified', '-created',)

    def __unicode__(self):
        return u"<SiteConfigurationHistory: {site}, Last Modified: {modified} >".format(
            modified=self.modified,
            site=self.site,
        )

    def __repr__(self):
        return self.__unicode__()


@receiver(post_save, sender=SiteConfiguration)
def update_site_configuration_history(sender, instance, **kwargs):  # pylint: disable=unused-argument
    """
    Add site configuration changes to site configuration history.

    Args:
        sender: sender of the signal i.e. SiteConfiguration model
        instance: SiteConfiguration instance associated with the current signal
        **kwargs: extra key word arguments
    """
    SiteConfigurationHistory.objects.create(
        site=instance.site,
        values=instance.values,
        enabled=instance.enabled,
    )

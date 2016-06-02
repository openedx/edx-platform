"""
Models.
"""
from django.utils.translation import ugettext_lazy as _

from django.db.models import TextField

from config_models.models import ConfigurationModel
from django.db import models

from simple_history.models import HistoricalRecords


class XBlockDisableConfig(ConfigurationModel):
    """
    Configuration for disabling and deprecating XBlocks.
    """

    class Meta(ConfigurationModel.Meta):
        app_label = 'xblock_django'

    disabled_blocks = TextField(
        default='', blank=True,
        help_text=_('Space-separated list of XBlocks which should not render.')
    )

    disabled_create_blocks = TextField(
        default='', blank=True,
        help_text=_(
            "Space-separated list of XBlock types whose creation to disable in Studio."
        )
    )

    # @classmethod
    # def is_block_type_disabled(cls, block_type):
    #     """ Return True if block_type is disabled. """
    #
    #     config = cls.current()
    #     if not config.enabled:
    #         return False
    #
    #     return block_type in config.disabled_blocks.split()

    # @classmethod
    # def disabled_block_types(cls):
    #     """ Return list of disabled xblock types. """
    #
    #     config = cls.current()
    #     if not config.enabled:
    #         return ()
    #
    #     return config.disabled_blocks.split()

    # @classmethod
    # def disabled_create_block_types(cls):
    #     """ Return list of deprecated XBlock types. Merges types in settings file and field. """
    #
    #     config = cls.current()
    #     xblock_types = config.disabled_create_blocks.split() if config.enabled else []
    #
    #     # Merge settings list with one in the admin config;
    #     if hasattr(settings, 'DEPRECATED_ADVANCED_COMPONENT_TYPES'):
    #         xblock_types.extend(
    #             xblock_type for xblock_type in settings.DEPRECATED_ADVANCED_COMPONENT_TYPES
    #             if xblock_type not in xblock_types
    #         )
    #
    #     return xblock_types
    #
    # def __unicode__(self):
    #     config = XBlockDisableConfig.current()
    #     return u"Disabled xblocks = {disabled_xblocks}\nDeprecated xblocks = {disabled_create_block_types}".format(
    #         disabled_xblocks=config.disabled_blocks,
    #         disabled_create_block_types=config.disabled_create_block_types
    #     )



class XBlockConfigFlag(ConfigurationModel):
    """
    Enables site-wide configuration for xblock support state.
    """

    class Meta(object):
        app_label = "xblock_django"


class XBlockConfig(models.Model):
    """
    Configuration for a specific xblock. Currently used for support state.
    """
    FULL_SUPPORT = 'fs'
    PROVISIONAL_SUPPORT = 'ps'
    UNSUPPORTED_OPT_IN = 'ua'
    UNSUPPORTED_NO_OPT_IN = 'ud'
    DISABLED = 'da'

    SUPPORT_CHOICES = (
        (FULL_SUPPORT, _('Fully Supported')),
        (PROVISIONAL_SUPPORT, _('Provisionally Supported')),
        (UNSUPPORTED_OPT_IN, _('Unsupported (Opt-in allowed)')),
        (UNSUPPORTED_NO_OPT_IN, _('Unsupported (Opt-in disallowed)')),
        (DISABLED, _('Disabled')),
    )

    # for archiving
    # history = HistoricalRecords()

    name = models.CharField(max_length=255, null=False)
    template = models.CharField(max_length=255, blank=True, default='')
    support_level = models.CharField(max_length=2, choices=SUPPORT_CHOICES, default=UNSUPPORTED_NO_OPT_IN)
    deprecated = models.BooleanField(
        default=False,
        verbose_name=_('show deprecation messaging in Studio'),
        help_text=_("Only xblocks listed in a course's Advanced Module List can be flagged as deprecated. Note that deprecation is by xblock name, and is not specific to template.")
    )

    class Meta(object):
        app_label = "xblock_django"
        unique_together = ("name", "template")

    @classmethod
    def deprecated_xblocks(cls):
        """ Return the QuerySet of deprecated XBlock types. """
        return cls.objects.filter(deprecated=True)

    @classmethod
    def disabled_xblocks(cls):
        """ Return the QuerySet of XBlocks that are disabled. """
        return cls.objects.filter(support_level=cls.DISABLED)

    @classmethod
    def authorable_xblocks(cls, limited_support_opt_in=False, name=None):
        """
        Return the QuerySet of XBlocks that can be created in Studio. Note that this method
        looks only at `support_level` and does not take into account `deprecated`.

        Arguments:
            limited_support_opt_in (bool): If `True`, XBlocks with limited support will be included.
                Default value is `False`.
            name (str): If provided, filters the returned XBlocks to those with the provided name. This is
                useful for XBlocks with lots of template types.

        Returns:
            QuerySet: Authorable XBlocks, taking into account `support_level` and `name` (if specified).

        """
        blocks = cls.objects.exclude(support_level=cls.DISABLED).exclude(support_level=cls.UNSUPPORTED_NO_OPT_IN)
        if not limited_support_opt_in:
            blocks = blocks.exclude(support_level=cls.UNSUPPORTED_OPT_IN).exclude(support_level=cls.PROVISIONAL_SUPPORT)

        if name:
            blocks = blocks.filter(name=name)

        return blocks

    def __unicode__(self):
        return (
            "[XBlockConfig] '{}': template='{}', support level='{}', deprecated={}"
        ).format(self.name, self.template, self.support_level, self.deprecated)

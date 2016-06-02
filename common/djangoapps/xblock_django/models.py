"""
Models.
"""
from django.utils.translation import ugettext_lazy as _

from django.conf import settings

from django.db.models import TextField

from config_models.models import ConfigurationModel
from django.db import models
from django.contrib.auth.models import User

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

    @classmethod
    def is_block_type_disabled(cls, block_type):
        """ Return True if block_type is disabled. """

        config = cls.current()
        if not config.enabled:
            return False

        return block_type in config.disabled_blocks.split()

    @classmethod
    def disabled_block_types(cls):
        """ Return list of disabled xblock types. """

        config = cls.current()
        if not config.enabled:
            return ()

        return config.disabled_blocks.split()

    @classmethod
    def disabled_create_block_types(cls):
        """ Return list of deprecated XBlock types. Merges types in settings file and field. """

        config = cls.current()
        xblock_types = config.disabled_create_blocks.split() if config.enabled else []

        # Merge settings list with one in the admin config;
        if hasattr(settings, 'DEPRECATED_ADVANCED_COMPONENT_TYPES'):
            xblock_types.extend(
                xblock_type for xblock_type in settings.DEPRECATED_ADVANCED_COMPONENT_TYPES
                if xblock_type not in xblock_types
            )

        return xblock_types

    def __unicode__(self):
        config = XBlockDisableConfig.current()
        return u"Disabled xblocks = {disabled_xblocks}\nDeprecated xblocks = {disabled_create_block_types}".format(
            disabled_xblocks=config.disabled_blocks,
            disabled_create_block_types=config.disabled_create_block_types
        )


class XBlockConfigFlag(ConfigurationModel):
    """
    Enables site-wide configuration for xblock support state.
    """

    class Meta(object):
        app_label = "xblock_django"

    def __unicode__(self):
        return "[XBlockConfigFlag] enabled={}".format(self.enabled)


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
        # May lack robustness, course staff should test.
        (PROVISIONAL_SUPPORT, _('Provisionally Supported')),
        # Unsupported, may not meet edX standards.
        (UNSUPPORTED_OPT_IN, _('Unsupported (Opt-in allowed)')),
        # Used when deprecating components, never allowed to create in Studio.
        (UNSUPPORTED_NO_OPT_IN, _('Unsupported (Opt-in disallowed)')),
        # Will not render in the LMS
        (DISABLED, _('Disabled')),
    )

    # for archiving
    history = HistoricalRecords()
    change_date = models.DateTimeField(auto_now=True, verbose_name=_("change date"))
    changed_by = models.ForeignKey(
        User,
        editable=False,
        null=True,
        on_delete=models.PROTECT,
        # Translators: this label indicates the name of the user who made this change:
        verbose_name=_("changed by"),
    )

    name = models.CharField(max_length=255, null=False)
    template = models.CharField(max_length=255, blank=True, default='')
    support_level = models.CharField(max_length=2, choices=SUPPORT_CHOICES, default=UNSUPPORTED_NO_OPT_IN)
    deprecated = models.BooleanField(
        default=False,
        verbose_name=_('show deprecation messaging in Studio'),
        help_text=_(
            "Only XBlocks listed in a course's Advanced Module List can be flagged as deprecated. "
            "Note that deprecation is by XBlock name, and is not specific to template.")
    )

    class Meta(object):
        app_label = "xblock_django"
        unique_together = ("name", "template")

    @property
    def _history_user(self):
        """ Show in history the user who made the last change. """
        return self.changed_by

    @_history_user.setter
    def _history_user(self, value):
        """ Show in history the user who made the last change. """
        self.changed_by = value

    @property
    def _history_date(self):
        """ Show in history the date of the last change. """
        return self.change_date

    @_history_date.setter
    def _history_date(self, value):
        """ Show in history the date of the last change. """
        self.change_date = value

    @classmethod
    def deprecated_xblocks(cls):
        """ Return the QuerySet of deprecated XBlock types. """
        return cls.objects.filter(deprecated=True)

    @classmethod
    def disabled_xblocks(cls):
        """ Return the QuerySet of XBlocks that are disabled. """
        return cls.objects.filter(support_level=cls.DISABLED)

    @classmethod
    def authorable_xblocks(cls, allow_unsupported=False, name=None):
        """
        Return the QuerySet of XBlocks that can be created in Studio (by default, only fully supported and
        provisionally supported). Note that this method looks only at `support_level` and does not take into
        account `deprecated`.
        Arguments:
            allow_unsupported (bool): If `True`, unsupported XBlocks that are flagged as allowing opt-in
                will also be returned. Note that unsupported XBlocks are not recommended for use in courses
                due to non-compliance with one or more of the base requirements, such as testing, accessibility,
                internationalization, and documentation. Default value is `False`.
            name (str): If provided, filters the returned XBlocks to those with the provided name. This is
                useful for XBlocks with lots of template types.
        Returns:
            QuerySet: Authorable XBlocks, taking into account `support_level` and `name` (if specified).
        """
        blocks = cls.objects.exclude(support_level=cls.DISABLED).exclude(support_level=cls.UNSUPPORTED_NO_OPT_IN)
        if not allow_unsupported:
            blocks = blocks.exclude(support_level=cls.UNSUPPORTED_OPT_IN)

        if name:
            blocks = blocks.filter(name=name)

        return blocks

    def __unicode__(self):
        return (
            "[XBlockConfig] '{}': template='{}', support level='{}', deprecated={}"
        ).format(self.name, self.template, self.support_level, self.deprecated)

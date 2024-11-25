"""
Course home api models file
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from openedx.core.djangoapps.config_model_utils.models import StackedConfigurationModel


class DisableProgressPageStackedConfig(StackedConfigurationModel):
    """
    Stacked Config Model for disabling the frontend-app-learning progress page
<<<<<<< HEAD
=======

    .. no_pii:
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
    """

    STACKABLE_FIELDS = ('disabled',)
    # Since this config disables the progress page,
    # it seemed it would be clearer to use a disabled flag instead of an enabled flag.
    # The enabled field still exists but is not used or shown in the admin.
    disabled = models.BooleanField(default=None, verbose_name=_("Disabled"), null=True)

    def __str__(self):
        return "DisableProgressPageStackedConfig(disabled={!r})".format(
            self.disabled
        )

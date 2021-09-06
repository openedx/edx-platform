"""
Django Admin for Block Structures.
"""


from config_models.admin import ConfigurationModelAdmin
from django.contrib import admin

from .config.models import BlockStructureConfiguration


class BlockStructureAdmin(ConfigurationModelAdmin):
    """
    Configuration Admin for BlockStructureConfiguration.
    """
    def get_displayable_field_names(self):
        """
        Excludes unused 'enabled field from super's list.
        """
        displayable_field_names = super(BlockStructureAdmin, self).get_displayable_field_names()
        displayable_field_names.remove('enabled')
        return displayable_field_names


admin.site.register(BlockStructureConfiguration, BlockStructureAdmin)

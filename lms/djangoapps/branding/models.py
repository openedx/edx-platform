"""
Models used by LMS XBlock infrastructure.

Includes:
    XBlockAsidesConfig: A ConfigurationModel for managing how XBlockAsides are
        rendered in the LMS.
"""

from django.db.models import URLField, TextField

from config_models.models import ConfigurationModel


class BrandingInfo(ConfigurationModel):
    """
    Configuration for Branding.
    """
    url = URLField(
        help_text="Link to the site."
    )

    logo_src = URLField(
        help_text="A source for the logo."
    )

    logo_tag = TextField(
        help_text="Text for the logo."
    )

    @classmethod
    def get_info(cls):
        """
        Get the list of status values to include files for in the encoding
        download
        """
        info = cls.current()
        return info if info.enabled else None

"""
Model used by Video module for Branding configuration.

Includes:
    BrandingInfoConfig: A ConfigurationModel for managing how Video Module will
        use Branding.
"""
import json
from django.db.models import TextField
from django.core.exceptions import ValidationError
from config_models.models import ConfigurationModel


class BrandingInfoConfig(ConfigurationModel):
    """
    Configuration for Branding.

    Example of configuration that must be stored:
        {
            "CN": {
                    "url": "http://www.xuetangx.com",
                    "logo_src": "http://www.xuetangx.com/static/images/logo.png",
                    "logo_tag": "Video hosted by XuetangX.com"
            }
        }
    """
    class Meta(ConfigurationModel.Meta):
        app_label = "branding"

    configuration = TextField(
        help_text="JSON data of Configuration for Video Branding."
    )

    def clean(self):
        """
        Validates configuration text field.
        """
        try:
            json.loads(self.configuration)
        except ValueError:
            raise ValidationError('Must be valid JSON string.')

    @classmethod
    def get_config(cls):
        """
        Get the Video Branding Configuration.
        """
        info = cls.current()
        return json.loads(info.configuration) if info.enabled else {}


class BrandingApiConfig(ConfigurationModel):
    """Configure Branding api's

    Enable or disable api's functionality.
    When this flag is disabled, the api will return 404.

    When the flag is enabled, the api will returns the valid reponse.
    """
    class Meta(ConfigurationModel.Meta):
        app_label = "branding"

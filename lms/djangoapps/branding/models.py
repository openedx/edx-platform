"""
Model used by Video module for Branding configuration.

Updated to also support organizations

Includes:
    BrandingInfoConfig: A ConfigurationModel for managing how Video Module will
        use Branding.
"""
import json
from django.db import models
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


def img_name(instance, filename):
    ext = filename.split('.')[-1]
    if not ext:
        ext = 'jpg'
    return 'organization/' + instance.name + '.' + ext

class Organization(models.Model):
    name        = models.CharField( max_length = 255 )
    image       = models.ImageField( blank = True, null = True, upload_to = img_name )
    about_short = models.TextField( blank = True, null = True )
    about_long  = models.TextField( blank = True, null = True )


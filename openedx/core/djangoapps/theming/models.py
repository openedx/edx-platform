"""
Django models supporting the Comprehensive Theming subsystem
"""
from django.db import models
from django.conf import settings
from django.contrib.sites.models import Site


class SiteTheme(models.Model):
    """
    This is where the information about the site's theme gets stored to the db.

    `site` field is foreignkey to django Site model
    `theme_dir_name` contains directory name having Site's theme
    """
    site = models.ForeignKey(Site, related_name='themes')
    theme_dir_name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.theme_dir_name

    @staticmethod
    def get_theme(site, default=None):
        """
        Get SiteTheme object for given site, returns default site theme if it can not
        find a theme for the given site and `DEFAULT_SITE_THEME` setting has a proper value.

        Args:
            site (django.contrib.sites.models.Site): site object related to the current site.
            default (openedx.core.djangoapps.models.SiteTheme): site theme object to return in case there is no theme
                associated for the given site.

        Returns:
            SiteTheme object for given site or a default site passed in as the argument.
        """

        theme = site.themes.first()
        return theme or default

    @staticmethod
    def has_theme(site):
        """
        Returns True if given site has an associated site theme in database, returns False otherwise.
        Note: DEFAULT_SITE_THEME is not considered as an associated site.

        Args:
            site (django.contrib.sites.models.Site): site object related to the current site.

        Returns:
            True if given site has an associated site theme in database, returns False otherwise.
        """
        return site.themes.exists()

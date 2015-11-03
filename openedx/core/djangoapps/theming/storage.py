import os
import urlparse
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.encoding import filepath_to_uri
from django.utils._os import safe_join


class ComprehensiveThemingAwareMixin(object):
    """
    Mixin for Django storage system to make it aware of the currently-active
    comprehensive theme, so that it can generate theme-scoped URLs for themed
    static assets.
    """
    def __init__(self, *args, **kwargs):
        super(ComprehensiveThemingAwareMixin, self).__init__(*args, **kwargs)
        COMP_THEME_DIR = getattr(settings, "COMP_THEME_DIR", "")  # pylint: disable=invalid-name
        if not COMP_THEME_DIR:
            self.theme_location = None
            return

        if not isinstance(COMP_THEME_DIR, basestring):
            raise ImproperlyConfigured("Your COMP_THEME_DIR setting must be a string")

        PROJECT_ROOT = getattr(settings, "PROJECT_ROOT", "")  # pylint: disable=invalid-name
        if PROJECT_ROOT.endswith("cms"):
            system = "studio"
        else:
            system = "lms"
        self.theme_location = os.path.join(COMP_THEME_DIR, system, "static")

    def themed(self, name):
        """
        Given a name, return a boolean indicating whether that name exists
        as a themed asset in the comprehensive theme.
        """
        # Nothing can be themed if we don't have a theme location.
        if not self.theme_location:
            return False

        try:
            path = safe_join(self.theme_location, name)
        except ValueError:
            raise SuspiciousOperation("Attempted access to '%s' denied." % name)
        return os.path.exists(os.path.normpath(path))

    def path(self, name):
        if self.themed(name):
            base = self.theme_location
        else:
            base = self.location
        try:
            path = safe_join(base, name)
        except ValueError:
            raise SuspiciousOperation("Attempted access to '%s' denied." % name)
        return os.path.normpath(path)

    def url(self, name):
        if self.themed(name):
            theme_name = os.path.basename(os.path.normpath(settings.COMP_THEME_DIR))
            # note that self.base_url will be settings.STATIC_URL, which is
            # assumed to end in a slash (as per Django's documentation)
            base_url = "{base_url}themes/{theme_name}/".format(
                base_url=self.base_url,
                theme_name=theme_name,
            )
        else:
            base_url = self.base_url

        return urlparse.urljoin(base_url, filepath_to_uri(name))



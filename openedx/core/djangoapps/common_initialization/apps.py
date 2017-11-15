"""
Common initialization app for the LMS and CMS
"""

from django.apps import AppConfig
from django.conf import settings


class CommonInitializationConfig(AppConfig):
    name = 'openedx.core.djangoapps.common_initialization'
    verbose_name = 'Common Initialization'

    def ready(self):
        # Common settings validations for the LMS and CMS.
        from . import checks

        self._add_mimetypes()

        if not acceptable_domain_name(settings.SITE_NAME):
            raise Exception(
                "SITE_NAME is not an allowed domain name: %r. "
                "See https://openedx.atlassian.net/wiki/x/ewFNEw for more information."
                % (settings.SITE_NAME,)
            )

    def _add_mimetypes(self):
        """
        Add extra mimetypes. Used in xblock_resource.
        """
        import mimetypes

        mimetypes.add_type('application/vnd.ms-fontobject', '.eot')
        mimetypes.add_type('application/x-font-opentype', '.otf')
        mimetypes.add_type('application/x-font-ttf', '.ttf')
        mimetypes.add_type('application/font-woff', '.woff')


def acceptable_domain_name(domain):
    """
    Check that a domain is an acceptable use of edX trademarks.

    99% of the problem we are trying to solve is "edx.toplevel.com", so don't
    go nuts trying to deal with all of the complexity of domain names.

    Returns True if the domain is ok.

    """
    host, _, _ = domain.partition(':')
    ret = True

    # Special-case some of our own domain names.
    if host in ["edx.org", "edx.devstack.lms"]:
        ret = True
    else:
        # We don't want people to use "edx." as a subdomain, to protect the
        # edX trademark.
        parts = host.split(".")
        if "edx" in parts:
            ret = False

    return ret

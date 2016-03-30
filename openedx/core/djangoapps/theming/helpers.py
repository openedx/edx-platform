"""
    Helpers for accessing comprehensive theming related variables.
"""
import re
import os
from path import Path

from django.conf import settings, ImproperlyConfigured
from django.core.cache import cache
from django.contrib.staticfiles.storage import staticfiles_storage

from microsite_configuration import microsite
from microsite_configuration import page_title_breadcrumbs


def get_page_title_breadcrumbs(*args):
    """
    This is a proxy function to hide microsite_configuration behind comprehensive theming.
    """
    return page_title_breadcrumbs(*args)


def get_value(val_name, default=None, **kwargs):
    """
    This is a proxy function to hide microsite_configuration behind comprehensive theming.
    """
    return microsite.get_value(val_name, default=default, **kwargs)


def get_template_path(relative_path, **kwargs):
    """
    This is a proxy function to hide microsite_configuration behind comprehensive theming.
    """
    template_path = get_template_path_with_theme(relative_path)
    if template_path == relative_path:  # we don't have a theme now look into microsites
        template_path = microsite.get_template_path(relative_path, **kwargs)

    return template_path


def is_request_in_themed_site():
    """
    This is a proxy function to hide microsite_configuration behind comprehensive theming.
    """
    return microsite.is_request_in_microsite()


def get_template(uri):
    """
    This is a proxy function to hide microsite_configuration behind comprehensive theming.
    :param uri: uri of the template
    """
    return microsite.get_template(uri)


def get_themed_template_path(relative_path, default_path, **kwargs):
    """
    This is a proxy function to hide microsite_configuration behind comprehensive theming.

    The workflow considers the "Stanford theming" feature alongside of microsites.  It returns
    the path of the themed template (i.e. relative_path) if Stanford theming is enabled AND
    microsite theming is disabled, otherwise it will return the path of either the microsite
    override template or the base lms template.

    :param relative_path: relative path of themed template
    :param default_path: relative path of the microsite's or lms template to use if
        theming is disabled or microsite is enabled
    """
    is_stanford_theming_enabled = settings.FEATURES.get("USE_CUSTOM_THEME", False)
    is_microsite = microsite.is_request_in_microsite()
    if is_stanford_theming_enabled and not is_microsite:
        return relative_path
    return microsite.get_template_path(default_path, **kwargs)


def get_template_path_with_theme(relative_path):
    """
    Returns template path in current site's theme if it finds one there otherwise returns same path.

    Example:
        >> get_template_path_with_theme('header')
        '/red-theme/lms/templates/header.html'

    Parameters:
        relative_path (str): template's path relative to the templates directory e.g. 'footer.html'

    Returns:
        (str): template path in current site's theme
    """
    site_theme_dir = get_current_site_theme_dir()
    if not site_theme_dir:
        return relative_path

    base_theme_dir = get_base_theme_dir()
    root_name = get_project_root_name()
    template_path = "/".join([
        base_theme_dir,
        site_theme_dir,
        root_name,
        "templates"
    ])

    # strip `/` if present at the start of relative_path
    template_name = re.sub(r'^/+', '', relative_path)
    search_path = os.path.join(template_path, template_name)
    if os.path.isfile(search_path):
        path = '/{site_theme_dir}/{root_name}/templates/{template_name}'.format(
            site_theme_dir=site_theme_dir,
            root_name=root_name,
            template_name=template_name,
        )
        return path
    else:
        return relative_path


def get_current_theme_template_dirs():
    """
    Returns template directories for the current theme.

    Example:
        >> get_current_theme_template_dirs('header.html')
        ['/edx/app/edxapp/edx-platform/themes/red-theme/lms/templates/', ]

    Returns:
        (list): list of directories containing theme templates.
    """
    site_theme_dir = get_current_site_theme_dir()
    if not site_theme_dir:
        return None

    base_theme_dir = get_base_theme_dir()
    root_name = get_project_root_name()
    template_path = "/".join([
        base_theme_dir,
        site_theme_dir,
        root_name,
        "templates"
    ])

    return [template_path]


def strip_site_theme_templates_path(uri):
    """
    Remove site template theme path from the uri.

    Example:
        >> strip_site_theme_templates_path('/red-theme/lms/templates/header.html')
        'header.html'

    Arguments:
        uri (str): template path from which to remove site theme path. e.g. '/red-theme/lms/templates/header.html'

    Returns:
        (str): template path with site theme path removed.
    """
    site_theme_dir = get_current_site_theme_dir()
    if not site_theme_dir:
        return uri

    root_name = get_project_root_name()
    templates_path = "/".join([
        site_theme_dir,
        root_name,
        "templates"
    ])

    uri = re.sub(r'^/*' + templates_path + '/*', '', uri)
    return uri


def get_current_site():
    """
    Return current site.

    Returns:
         (django.contrib.sites.models.Site): theme directory for current site
    """
    from edxmako.middleware import REQUEST_CONTEXT
    request = getattr(REQUEST_CONTEXT, 'request', None)
    if not request:
        return None
    return getattr(request, 'site', None)


def get_current_site_theme_dir():
    """
    Return theme directory for the current site.

    Example:
        >> get_current_site_theme_dir()
        'red-theme'

    Returns:
         (str): theme directory for current site
    """
    site = get_current_site()
    if not site:
        return None
    site_theme_dir = cache.get(get_site_theme_cache_key(site))

    # if site theme dir is not in cache and comprehensive theming is enabled then pull it from db.
    if not site_theme_dir and is_comprehensive_theming_enabled():
        site_theme = site.themes.first()  # pylint: disable=no-member
        if site_theme:
            site_theme_dir = site_theme.theme_dir_name
            cache_site_theme_dir(site, site_theme_dir)
    return site_theme_dir


def get_project_root_name():
    """
    Return root name for the current project

    Example:
        >> get_project_root_name()
        'lms'
        # from studio
        >> get_project_root_name()
        'cms'

    Returns:
        (str): component name of platform e.g lms, cms
    """
    root = Path(settings.PROJECT_ROOT)
    if root.name == "":
        root = root.parent
    return root.name


def get_base_theme_dir():
    """
    Return base directory that contains all the themes.

    Example:
        >> get_base_theme_dir()
        '/edx/app/edxapp/edx-platform/themes'

    Returns:
         (Path): Base theme directory path
    """
    themes_dir = settings.COMPREHENSIVE_THEME_DIR
    if not isinstance(themes_dir, basestring):
        raise ImproperlyConfigured("COMPREHENSIVE_THEME_DIR must be a string.")
    return Path(themes_dir)


def is_comprehensive_theming_enabled():
    """
    Returns boolean indicating whether comprehensive theming functionality is enabled or disabled.
    Example:
        >> is_comprehensive_theming_enabled()
        True

    Returns:
         (bool): True if comprehensive theming is enabled else False
    """
    return True if settings.COMPREHENSIVE_THEME_DIR else False


def get_site_theme_cache_key(site):
    """
    Return cache key for the given site.

    Example:
        >> site = Site(domain='red-theme.org', name='Red Theme')
        >> get_site_theme_cache_key(site)
        'theming.site.red-theme.org'

    Parameters:
        site (django.contrib.sites.models.Site): site where key needs to generated
    Returns:
        (str): a key to be used as cache key
    """
    cache_key = "theming.site.{domain}".format(
        domain=site.domain
    )
    return cache_key


def cache_site_theme_dir(site, theme_dir):
    """
    Cache site's theme directory.

    Example:
        >> site = Site(domain='red-theme.org', name='Red Theme')
        >> cache_site_theme_dir(site, 'red-theme')

    Parameters:
        site (django.contrib.sites.models.Site): site for to cache
        theme_dir (str): theme directory for the given site
    """
    cache.set(get_site_theme_cache_key(site), theme_dir, settings.THEME_CACHE_TIMEOUT)


def get_static_file_url(asset):
    """
    Returns url of the themed asset if asset is not themed than returns the default asset url.

    Example:
        >> get_static_file_url('css/lms-main.css')
        '/static/red-theme/css/lms-main.css'

    Parameters:
        asset (str): asset's path relative to the static files directory

    Returns:
        (str): static asset's url
    """
    return staticfiles_storage.url(asset)


def get_themes():
    """
    get a list of all themes known to the system.
    Returns:
        list of themes known to the system.
    """
    themes_dir = get_base_theme_dir()
    # pick only directories and discard files in themes directory
    theme_names = []
    if themes_dir:
        theme_names = [_dir for _dir in os.listdir(themes_dir) if is_theme_dir(themes_dir / _dir)]

    return [Theme(name, name) for name in theme_names]


def is_theme_dir(_dir):
    """
    Returns true if given dir contains theme overrides.
    A theme dir must have subdirectory 'lms' or 'cms' or both.

    Args:
        _dir: directory path to check for a theme

    Returns:
        Returns true if given dir is a theme directory.
    """
    theme_sub_directories = {'lms', 'cms'}
    return bool(os.path.isdir(_dir) and theme_sub_directories.intersection(os.listdir(_dir)))


class Theme(object):
    """
    class to encapsulate theme related information.
    """
    name = ''
    theme_dir = ''
    path = ''

    def __init__(self, name='', theme_dir=''):
        """
        init method for Theme
        Args:
            name: name if the theme
            theme_dir: directory name of the theme
        """
        self.name = name
        self.theme_dir = theme_dir
        self.path = Path(get_base_theme_dir()) / theme_dir / get_project_root_name()

    def __eq__(self, other):
        """
        Returns True if given theme is same as the self
        Args:
            other: Theme object to compare with self

        Returns:
            (bool) True if two themes are the same else False
        """
        return (self.theme_dir, self.path) == (other.theme_dir, other.path)

    def __hash__(self):
        return hash((self.theme_dir, self.path))

    def __unicode__(self):
        return u"<Theme: {name} at '{path}'>".format(name=self.name, path=self.path)

    def __repr__(self):
        return self.__unicode__()

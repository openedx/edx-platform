"""
Helpers for accessing comprehensive theming related variables.
"""
import re
import os
from path import Path

from django.conf import settings, ImproperlyConfigured
from django.contrib.staticfiles.storage import staticfiles_storage

from request_cache.middleware import RequestCache

from microsite_configuration import microsite, page_title_breadcrumbs

from logging import getLogger
logger = getLogger(__name__)  # pylint: disable=invalid-name


def get_page_title_breadcrumbs(*args):
    """
    This is a proxy function to hide microsite_configuration behind comprehensive theming.
    """
    return page_title_breadcrumbs(*args)


def get_value(val_name, default=None, **kwargs):
    """
    This is a proxy function to hide microsite_configuration behind comprehensive theming.
    """

    # Retrieve the requested field/value from the microsite configuration
    microsite_value = microsite.get_value(val_name, default=default, **kwargs)

    # Attempt to perform a dictionary update using the provided default
    # This will fail if either the default or the microsite value is not a dictionary
    try:
        value = dict(default)
        value.update(microsite_value)

    # If the dictionary update fails, just use the microsite value
    # TypeError: default is not iterable (simple value or None)
    # ValueError: default is iterable but not a dict (list, not dict)
    # AttributeError: default does not have an 'update' method
    except (TypeError, ValueError, AttributeError):
        value = microsite_value

    # Return the end result to the caller
    return value


def get_template_path(relative_path, **kwargs):
    """
    This is a proxy function to hide microsite_configuration behind comprehensive theming.
    """
    if microsite.is_request_in_microsite():
        relative_path = microsite.get_template_path(relative_path, **kwargs)
    return relative_path


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
        >> get_template_path_with_theme('header.html')
        '/red-theme/lms/templates/header.html'

    Parameters:
        relative_path (str): template's path relative to the templates directory e.g. 'footer.html'

    Returns:
        (str): template path in current site's theme
    """
    theme = get_current_theme()

    if not theme:
        return relative_path

    # strip `/` if present at the start of relative_path
    template_name = re.sub(r'^/+', '', relative_path)

    template_path = theme.template_path / template_name
    absolute_path = theme.path / "templates" / template_name
    if absolute_path.exists():
        return str(template_path)
    else:
        return relative_path


def get_all_theme_template_dirs():
    """
    Returns template directories for all the themes.

    Example:
        >> get_all_theme_template_dirs()
        [
            '/edx/app/edxapp/edx-platform/themes/red-theme/lms/templates/',
        ]

    Returns:
        (list): list of directories containing theme templates.
    """
    themes = get_themes()
    template_paths = list()

    for theme in themes:
        template_paths.extend(theme.template_dirs)

    return template_paths


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
    theme = get_current_theme()

    if not theme:
        return uri

    templates_path = "/".join([
        theme.theme_dir_name,
        get_project_root_name(),
        "templates"
    ])

    uri = re.sub(r'^/*' + templates_path + '/*', '', uri)
    return uri


def get_current_request():
    """
    Return current request instance.

    Returns:
         (HttpRequest): returns cirrent request
    """
    return RequestCache.get_current_request()


def get_current_site():
    """
    Return current site.

    Returns:
         (django.contrib.sites.models.Site): returns current site
    """
    request = get_current_request()
    if not request:
        return None
    return getattr(request, 'site', None)


def get_current_site_theme():
    """
    Return current site theme object. Returns None if theming is disabled.

    Returns:
         (ecommerce.theming.models.SiteTheme): site theme object for the current site.
    """
    # Return None if theming is disabled
    if not is_comprehensive_theming_enabled():
        return None

    request = get_current_request()
    if not request:
        return None
    return getattr(request, 'site_theme', None)


def get_current_theme():
    """
    Return current theme object. Returns None if theming is disabled.

    Returns:
         (ecommerce.theming.models.SiteTheme): site theme object for the current site.
    """
    # Return None if theming is disabled
    if not is_comprehensive_theming_enabled():
        return None

    site_theme = get_current_site_theme()
    if not site_theme:
        return None
    try:
        return Theme(
            name=site_theme.theme_dir_name,
            theme_dir_name=site_theme.theme_dir_name,
            themes_base_dir=get_theme_base_dir(site_theme.theme_dir_name),
        )
    except ValueError as error:
        # Log exception message and return None, so that open source theme is used instead
        logger.exception('Theme not found in any of the themes dirs. [%s]', error)
        return None


def get_theme_base_dir(theme_dir_name, suppress_error=False):
    """
    Returns absolute path to the directory that contains the given theme.

    Args:
        theme_dir_name (str): theme directory name to get base path for
        suppress_error (bool): if True function will return None if theme is not found instead of raising an error
    Returns:
        (str): Base directory that contains the given theme
    """
    for themes_dir in get_theme_base_dirs():
        if theme_dir_name in get_theme_dirs(themes_dir):
            return themes_dir

    if suppress_error:
        return None

    raise ValueError(
        "Theme '{theme}' not found in any of the following themes dirs, \nTheme dirs: \n{dir}".format(
            theme=theme_dir_name,
            dir=get_theme_base_dirs(),
        ))


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


def get_theme_base_dirs():
    """
    Return base directory that contains all the themes.

    Raises:
        ImproperlyConfigured - exception is raised if
            1 - COMPREHENSIVE_THEME_DIRS is not a list
            1 - theme dir path is not a string
            2 - theme dir path is not an absolute path
            3 - path specified in COMPREHENSIVE_THEME_DIRS does not exist

    Example:
        >> get_theme_base_dirs()
        ['/edx/app/ecommerce/ecommerce/themes']

    Returns:
         (Path): Base theme directory path
    """
    # Return an empty list if theming is disabled
    if not is_comprehensive_theming_enabled():
        return []

    theme_base_dirs = []

    # Legacy code for COMPREHENSIVE_THEME_DIR backward compatibility
    if hasattr(settings, "COMPREHENSIVE_THEME_DIR"):
        theme_dir = settings.COMPREHENSIVE_THEME_DIR

        if not isinstance(theme_dir, basestring):
            raise ImproperlyConfigured("COMPREHENSIVE_THEME_DIR must be a string.")
        if not theme_dir.startswith("/"):
            raise ImproperlyConfigured("COMPREHENSIVE_THEME_DIR must be an absolute paths to themes dir.")
        if not os.path.isdir(theme_dir):
            raise ImproperlyConfigured("COMPREHENSIVE_THEME_DIR must be a valid path.")

        theme_base_dirs.append(Path(theme_dir))

    if hasattr(settings, "COMPREHENSIVE_THEME_DIRS"):
        theme_dirs = settings.COMPREHENSIVE_THEME_DIRS

        if not isinstance(theme_dirs, list):
            raise ImproperlyConfigured("COMPREHENSIVE_THEME_DIRS must be a list.")
        if not all([isinstance(theme_dir, basestring) for theme_dir in theme_dirs]):
            raise ImproperlyConfigured("COMPREHENSIVE_THEME_DIRS must contain only strings.")
        if not all([theme_dir.startswith("/") for theme_dir in theme_dirs]):
            raise ImproperlyConfigured("COMPREHENSIVE_THEME_DIRS must contain only absolute paths to themes dirs.")
        if not all([os.path.isdir(theme_dir) for theme_dir in theme_dirs]):
            raise ImproperlyConfigured("COMPREHENSIVE_THEME_DIRS must contain valid paths.")

        theme_base_dirs.extend([Path(theme_dir) for theme_dir in theme_dirs])

    return theme_base_dirs


def is_comprehensive_theming_enabled():
    """
    Returns boolean indicating whether comprehensive theming functionality is enabled or disabled.
    Example:
        >> is_comprehensive_theming_enabled()
        True

    Returns:
         (bool): True if comprehensive theming is enabled else False
    """
    # Disable theming for microsites
    if microsite.is_request_in_microsite():
        return False

    return settings.ENABLE_COMPREHENSIVE_THEMING


def get_static_file_url(asset):
    """
    Returns url of the themed asset if asset is not themed than returns the default asset url.

    Example:
        >> get_static_file_url('css/lms-main-v1.css')
        '/static/red-theme/css/lms-main-v1.css'

    Parameters:
        asset (str): asset's path relative to the static files directory

    Returns:
        (str): static asset's url
    """
    return staticfiles_storage.url(asset)


def get_themes(themes_dir=None):
    """
    get a list of all themes known to the system.

    Args:
        themes_dir (str): (Optional) Path to themes base directory
    Returns:
        list of themes known to the system.
    """
    if not is_comprehensive_theming_enabled():
        return []

    themes_dirs = [Path(themes_dir)] if themes_dir else get_theme_base_dirs()
    # pick only directories and discard files in themes directory
    themes = []
    for themes_dir in themes_dirs:
        themes.extend([Theme(name, name, themes_dir) for name in get_theme_dirs(themes_dir)])

    return themes


def get_theme_dirs(themes_dir=None):
    """
    Returns theme dirs in given dirs
    Args:
        themes_dir (Path): base dir that contains themes.
    """
    return [_dir for _dir in os.listdir(themes_dir) if is_theme_dir(themes_dir / _dir)]


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
    theme_dir_name = ''
    themes_base_dir = None

    def __init__(self, name='', theme_dir_name='', themes_base_dir=None):
        """
        init method for Theme

        Args:
            name: name if the theme
            theme_dir_name: directory name of the theme
            themes_base_dir: directory path of the folder that contains the theme
        """
        self.name = name
        self.theme_dir_name = theme_dir_name
        self.themes_base_dir = themes_base_dir

    def __eq__(self, other):
        """
        Returns True if given theme is same as the self
        Args:
            other: Theme object to compare with self

        Returns:
            (bool) True if two themes are the same else False
        """
        return (self.theme_dir_name, self.path) == (other.theme_dir_name, other.path)

    def __hash__(self):
        return hash((self.theme_dir_name, self.path))

    def __unicode__(self):
        return u"<Theme: {name} at '{path}'>".format(name=self.name, path=self.path)

    def __repr__(self):
        return self.__unicode__()

    @property
    def path(self):
        """
        Get absolute path of the directory that contains current theme's templates, static assets etc.

        Returns:
            Path: absolute path to current theme's contents
        """
        return Path(self.themes_base_dir) / self.theme_dir_name / get_project_root_name()

    @property
    def template_path(self):
        """
        Get absolute path of current theme's template directory.

        Returns:
            Path: absolute path to current theme's template directory
        """
        return Path(self.theme_dir_name) / get_project_root_name() / 'templates'

    @property
    def template_dirs(self):
        """
        Get a list of all template directories for current theme.

        Returns:
            list: list of all template directories for current theme.
        """
        return [
            self.path / 'templates',
        ]

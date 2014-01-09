"""
Module for code that should run during LMS startup
"""

from django.conf import settings

# Force settings to run so that the python path is modified
settings.INSTALLED_APPS  # pylint: disable=W0104

from django_startup import autostartup
from xmodule.modulestore.django import modulestore


def run():
    """
    Executed during django startup
    """
    autostartup()

    # Trigger a forced initialization of our modulestores since this can take a
    # while to complete and we want this done before HTTP requests are accepted.
    if settings.INIT_MODULESTORE_ON_STARTUP:
        for store_name in settings.MODULESTORE:
            modulestore(store_name)

    if settings.FEATURES.get('USE_CUSTOM_THEME', False):
        enable_theme()
    if settings.FEATURES.get('MICROSITES', False):
        enable_microsites()


def enable_theme():
    """
    Enable the settings for a custom theme, whose files should be stored
    in ENV_ROOT/themes/THEME_NAME (e.g., edx_all/themes/stanford).
    """
    # Workaround for setting THEME_NAME to an empty
    # string which is the default due to this ansible
    # bug: https://github.com/ansible/ansible/issues/4812
    if settings.THEME_NAME == "":
        settings.THEME_NAME = None
        return

    assert settings.FEATURES['USE_CUSTOM_THEME']
    settings.FAVICON_PATH = 'themes/{name}/images/favicon.ico'.format(
        name=settings.THEME_NAME
    )

    # Calculate the location of the theme's files
    theme_root = settings.ENV_ROOT / "themes" / settings.THEME_NAME

    # Include the theme's templates in the template search paths
    settings.TEMPLATE_DIRS.append(theme_root / 'templates')
    settings.MAKO_TEMPLATES['main'].append(theme_root / 'templates')

    # Namespace the theme's static files to 'themes/<theme_name>' to
    # avoid collisions with default edX static files
    settings.STATICFILES_DIRS.append(
        (u'themes/{}'.format(settings.THEME_NAME), theme_root / 'static')
    )


def enable_microsites():
    assert settings.FEATURES["MICROSITES"]
    # add the microsite directory to the staticfiles directory
    settings.STATICFILES_DIRS.append(settings.ENV_ROOT / "microsites")
    settings.MAKO_TEMPLATES['microsites'].setdefault([])
    settings.TEMPLATE_CONTEXT_PROCESSORS.append(
        "student.context_processors.microsite_processor"
    )

    for subdomain, config in settings.MICROSITES.items():
        dirname = config.get("directory", subdomain)
        subdir = settings.ENV_ROOT / "microsites" / dirname
        if not subdir.isdir():
            raise RuntimeError("Microsite {name} does not have directory {dir}".format(
                name=subdomain, dir=subdir))
        template_dir = subdir / "templates"
        settings.TEMPLATE_DIRS.append(template_dir)
        settings.MAKO_TEMPLATES['microsites'].append(template_dir)

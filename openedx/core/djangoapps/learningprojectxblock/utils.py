import pkg_resources
import os

LEARNINGPROJECTXBLOCK_NAME = 'assignmentxblock-xblock'
XBLOCK_FOLDER_NAME = 'assignmentxblock'

LEARNINGPROJECTXBLOCK_DIR = pkg_resources.get_distribution(LEARNINGPROJECTXBLOCK_NAME).location
LEARNINGPROJECTXBLOCK_TEMPLATES_DIR = os.path.join(LEARNINGPROJECTXBLOCK_DIR, XBLOCK_FOLDER_NAME, 'templates')
LEARNINGPROJECTXBLOCK_LOCALE_PATH = os.path.join(LEARNINGPROJECTXBLOCK_DIR, XBLOCK_FOLDER_NAME, 'translations')

# for _make_mako_template_dirs
def add_learningprojectxblock_templates_dir(func):
    def wrapper(settings):
        dirs = func(settings)

        return dirs + [LEARNINGPROJECTXBLOCK_TEMPLATES_DIR]

    return wrapper

# for _make_locale_paths
def add_learningprojectxblock_locale_path(func):
    def wrapper(settings):
        locale_paths = func(settings)
        return locale_paths + [LEARNINGPROJECTXBLOCK_LOCALE_PATH]

    return wrapper

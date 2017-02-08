import logging

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.template.base import TemplateDoesNotExist
from django.template.loaders.filesystem import Loader as FilesystemLoader
from django.template.loaders.app_directories import Loader as AppDirectoriesLoader
from django.template import Engine

from edxmako.template import Template

from openedx.core.lib.tempdir import mkdtemp_clean

log = logging.getLogger(__name__)


class MakoLoader(object):
    """
    This is a Django loader object which will load the template as a
    Mako template if the first line is "## mako". It is based off BaseLoader
    in django.template.loader.
    We need this in order to be able to include mako templates inside main_django.html.
    """

    is_usable = False

    def __init__(self, base_loader):
        # base_loader is an instance of a BaseLoader subclass
        self.base_loader = base_loader

        module_directory = getattr(settings, 'MAKO_MODULE_DIR', None)

        if module_directory is None:
            log.warning("For more caching of mako templates, set the MAKO_MODULE_DIR in settings!")
            module_directory = mkdtemp_clean()

        self.module_directory = module_directory

    def __call__(self, template_name, template_dirs=None):
        return self.load_template(template_name, template_dirs)

    def load_template(self, template_name, template_dirs=None):
        source, file_path = self.load_template_source(template_name, template_dirs)

        # In order to allow dynamic template overrides, we need to cache templates based on their absolute paths
        # rather than relative paths, overriding templates would have same relative paths.
        module_directory = self.module_directory.rstrip("/") + "/{dir_hash}/".format(dir_hash=hash(file_path))

        if source.startswith("## mako\n"):
            # This is a mako template
            template = Template(filename=file_path,
                                module_directory=module_directory,
                                input_encoding='utf-8',
                                output_encoding='utf-8',
                                default_filters=['decode.utf8'],
                                encoding_errors='replace',
                                uri=template_name)
            return template, None
        else:
            # This is a regular template
            try:
                template = Engine.get_default().from_string(source)
                return template, None
            except ImproperlyConfigured:
                # Either no DjangoTemplates engine was configured -or- multiple engines
                # were configured, making the get_default() call above fail.
                raise
            except TemplateDoesNotExist:
                # If compiling the loaded template raises TemplateDoesNotExist, back off to
                # returning the source and display name for the requested template.
                # This allows for eventual correct identification of the actual template that does
                # not exist.
                return source, file_path

    def load_template_source(self, template_name, template_dirs=None):
        # Just having this makes the template load as an instance, instead of a class.
        return self.base_loader.load_template_source(template_name, template_dirs)

    def reset(self):
        self.base_loader.reset()


class MakoFilesystemLoader(MakoLoader):
    is_usable = True
    _accepts_engine_in_init = True

    def __init__(self, *args):
        MakoLoader.__init__(self, FilesystemLoader(*args))


class MakoAppDirectoriesLoader(MakoLoader):
    is_usable = True
    _accepts_engine_in_init = True

    def __init__(self, *args):
        MakoLoader.__init__(self, AppDirectoriesLoader(*args))

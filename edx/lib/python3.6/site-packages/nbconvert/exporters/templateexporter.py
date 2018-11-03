"""This module defines TemplateExporter, a highly configurable converter
that uses Jinja2 to export notebook files into different formats.
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import print_function, absolute_import

import os
import uuid
import json

from traitlets import HasTraits, Unicode, List, Dict, Bool, default, observe
from traitlets.config import Config
from traitlets.utils.importstring import import_item
from ipython_genutils import py3compat
from jinja2 import (
    TemplateNotFound, Environment, ChoiceLoader, FileSystemLoader, BaseLoader,
    DictLoader
)

from nbconvert import filters
from .exporter import Exporter

# Jinja2 extensions to load.
JINJA_EXTENSIONS = ['jinja2.ext.loopcontrols']

default_filters = {
        'indent': filters.indent,
        'markdown2html': filters.markdown2html,
        'markdown2asciidoc': filters.markdown2asciidoc,
        'ansi2html': filters.ansi2html,
        'filter_data_type': filters.DataTypeFilter,
        'get_lines': filters.get_lines,
        'highlight2html': filters.Highlight2HTML,
        'highlight2latex': filters.Highlight2Latex,
        'ipython2python': filters.ipython2python,
        'posix_path': filters.posix_path,
        'markdown2latex': filters.markdown2latex,
        'markdown2rst': filters.markdown2rst,
        'comment_lines': filters.comment_lines,
        'strip_ansi': filters.strip_ansi,
        'strip_dollars': filters.strip_dollars,
        'strip_files_prefix': filters.strip_files_prefix,
        'html2text': filters.html2text,
        'add_anchor': filters.add_anchor,
        'ansi2latex': filters.ansi2latex,
        'wrap_text': filters.wrap_text,
        'escape_latex': filters.escape_latex,
        'citation2latex': filters.citation2latex,
        'path2url': filters.path2url,
        'add_prompts': filters.add_prompts,
        'ascii_only': filters.ascii_only,
        'prevent_list_blocks': filters.prevent_list_blocks,
        'get_metadata': filters.get_metadata,
        'convert_pandoc': filters.convert_pandoc,
        'json_dumps': json.dumps,
}

class ExtensionTolerantLoader(BaseLoader):
    """A template loader which optionally adds a given extension when searching.

    Constructor takes two arguments: *loader* is another Jinja loader instance
    to wrap. *extension* is the extension, which will be added to the template
    name if finding the template without it fails. This should include the dot,
    e.g. '.tpl'.
    """
    def __init__(self, loader, extension):
        self.loader = loader
        self.extension = extension

    def get_source(self, environment, template):
        try:
            return self.loader.get_source(environment, template)
        except TemplateNotFound:
            if template.endswith(self.extension):
                raise TemplateNotFound(template)
            return self.loader.get_source(environment, template+self.extension)

    def list_templates(self):
        return self.loader.list_templates()


class TemplateExporter(Exporter):
    """
    Exports notebooks into other file formats.  Uses Jinja 2 templating engine
    to output new formats.  Inherit from this class if you are creating a new
    template type along with new filters/preprocessors.  If the filters/
    preprocessors provided by default suffice, there is no need to inherit from
    this class.  Instead, override the template_file and file_extension
    traits via a config file.

    Filters available by default for templates:

    {filters}
    """

    # finish the docstring
    __doc__ = __doc__.format(filters='- ' + '\n    - '.join(
        sorted(default_filters.keys())))

    _template_cached = None

    export_from_notebook = "custom"

    def _invalidate_template_cache(self, change=None):
        self._template_cached = None

    @property
    def template(self):
        if self._template_cached is None:
            self._template_cached = self._load_template()
        return self._template_cached

    _environment_cached = None

    def _invalidate_environment_cache(self, change=None):
        self._environment_cached = None
        self._invalidate_template_cache()

    @property
    def environment(self):
        if self._environment_cached is None:
            self._environment_cached = self._create_environment()
        return self._environment_cached

    @property
    def default_config(self):
        c = Config({
            'RegexRemovePreprocessor': {
                'enabled': True
                },
            'TagRemovePreprocessor': {
                'enabled': True
                }
            })
        c.merge(super(TemplateExporter, self).default_config)
        return c

    template_file = Unicode(
            help="Name of the template file to use"
    ).tag(config=True, affects_template=True)

    raw_template = Unicode('', help="raw template string").tag(affects_environment=True)

    _last_template_file = ""
    _raw_template_key = "<memory>"

    @observe('template_file')
    def _template_file_changed(self, change):
        new = change['new']
        if new == 'default':
            self.template_file = self.default_template
            return
        # check if template_file is a file path
        # rather than a name already on template_path
        full_path = os.path.abspath(new)
        if os.path.isfile(full_path):
            template_dir, template_file = os.path.split(full_path)
            if template_dir not in [ os.path.abspath(p) for p in self.template_path ]:
                self.template_path = [template_dir] + self.template_path
            self.template_file = template_file

    @default('template_file')
    def _template_file_default(self):
        return self.default_template

    @observe('raw_template')
    def _raw_template_changed(self, change):
        if not change['new']:
            self.template_file = self.default_template or self._last_template_file
        self._invalidate_template_cache()

    default_template = Unicode(u'').tag(affects_template=True)

    template_path = List(['.']).tag(config=True, affects_environment=True)

    default_template_path = Unicode(
        os.path.join("..", "templates"),
        help="Path where the template files are located."
    ).tag(affects_environment=True)

    template_skeleton_path = Unicode(
        os.path.join("..", "templates", "skeleton"),
        help="Path where the template skeleton files are located.",
    ).tag(affects_environment=True)

    #Extension that the template files use.
    template_extension = Unicode(".tpl").tag(config=True, affects_environment=True)

    exclude_input = Bool(False,
        help = "This allows you to exclude code cell inputs from all templates if set to True."
        ).tag(config=True)

    exclude_input_prompt = Bool(False,
        help = "This allows you to exclude input prompts from all templates if set to True."
        ).tag(config=True)

    exclude_output = Bool(False,
        help = "This allows you to exclude code cell outputs from all templates if set to True."
        ).tag(config=True)

    exclude_output_prompt = Bool(False,
        help = "This allows you to exclude output prompts from all templates if set to True."
        ).tag(config=True)

    exclude_code_cell = Bool(False,
        help = "This allows you to exclude code cells from all templates if set to True."
        ).tag(config=True)

    exclude_markdown = Bool(False,
        help = "This allows you to exclude markdown cells from all templates if set to True."
        ).tag(config=True)

    exclude_raw = Bool(False,
        help = "This allows you to exclude raw cells from all templates if set to True."
        ).tag(config=True)

    exclude_unknown = Bool(False,
        help = "This allows you to exclude unknown cells from all templates if set to True."
        ).tag(config=True)

    extra_loaders = List(
        help="Jinja loaders to find templates. Will be tried in order "
             "before the default FileSystem ones.",
    ).tag(affects_environment=True)

    filters = Dict(
        help="""Dictionary of filters, by name and namespace, to add to the Jinja
        environment."""
    ).tag(config=True, affects_environment=True)

    raw_mimetypes = List(
        help="""formats of raw cells to be included in this Exporter's output."""
    ).tag(config=True)

    @default('raw_mimetypes')
    def _raw_mimetypes_default(self):
        return [self.output_mimetype, '']

    def __init__(self, config=None, **kw):
        """
        Public constructor

        Parameters
        ----------
        config : config
            User configuration instance.
        extra_loaders : list[of Jinja Loaders]
            ordered list of Jinja loader to find templates. Will be tried in order
            before the default FileSystem ones.
        template : str (optional, kw arg)
            Template to use when exporting.
        """
        super(TemplateExporter, self).__init__(config=config, **kw)

        self.observe(self._invalidate_environment_cache,
                     list(self.traits(affects_environment=True)))
        self.observe(self._invalidate_template_cache,
                     list(self.traits(affects_template=True)))


    def _load_template(self):
        """Load the Jinja template object from the template file

        This is triggered by various trait changes that would change the template.
        """

        # this gives precedence to a raw_template if present
        with self.hold_trait_notifications():
            if self.template_file != self._raw_template_key:
                self._last_template_file = self.template_file
            if self.raw_template:
                self.template_file = self._raw_template_key

        if not self.template_file:
            raise ValueError("No template_file specified!")

        # First try to load the
        # template by name with extension added, then try loading the template
        # as if the name is explicitly specified.
        template_file = self.template_file
        self.log.debug("Attempting to load template %s", template_file)
        self.log.debug("    template_path: %s", os.pathsep.join(self.template_path))
        return self.environment.get_template(template_file)

    def from_notebook_node(self, nb, resources=None, **kw):
        """
        Convert a notebook from a notebook node instance.

        Parameters
        ----------
        nb : :class:`~nbformat.NotebookNode`
          Notebook node
        resources : dict
          Additional resources that can be accessed read/write by
          preprocessors and filters.
        """
        nb_copy, resources = super(TemplateExporter, self).from_notebook_node(nb, resources, **kw)
        resources.setdefault('raw_mimetypes', self.raw_mimetypes)
        resources['global_content_filter'] = {
                'include_code': not self.exclude_code_cell,
                'include_markdown': not self.exclude_markdown,
                'include_raw': not self.exclude_raw,
                'include_unknown': not self.exclude_unknown,
                'include_input': not self.exclude_input,
                'include_output': not self.exclude_output,
                'include_input_prompt': not self.exclude_input_prompt,
                'include_output_prompt': not self.exclude_output_prompt,
                'no_prompt': self.exclude_input_prompt and self.exclude_output_prompt,
                }

        # Top level variables are passed to the template_exporter here.
        output = self.template.render(nb=nb_copy, resources=resources)
        return output, resources

    def _register_filter(self, environ, name, jinja_filter):
        """
        Register a filter.
        A filter is a function that accepts and acts on one string.
        The filters are accessible within the Jinja templating engine.

        Parameters
        ----------
        name : str
            name to give the filter in the Jinja engine
        filter : filter
        """
        if jinja_filter is None:
            raise TypeError('filter')
        isclass = isinstance(jinja_filter, type)
        constructed = not isclass

        #Handle filter's registration based on it's type
        if constructed and isinstance(jinja_filter, py3compat.string_types):
            #filter is a string, import the namespace and recursively call
            #this register_filter method
            filter_cls = import_item(jinja_filter)
            return self._register_filter(environ, name, filter_cls)

        if constructed and hasattr(jinja_filter, '__call__'):
            #filter is a function, no need to construct it.
            environ.filters[name] = jinja_filter
            return jinja_filter

        elif isclass and issubclass(jinja_filter, HasTraits):
            #filter is configurable.  Make sure to pass in new default for
            #the enabled flag if one was specified.
            filter_instance = jinja_filter(parent=self)
            self._register_filter(environ, name, filter_instance)

        elif isclass:
            #filter is not configurable, construct it
            filter_instance = jinja_filter()
            self._register_filter(environ, name, filter_instance)

        else:
            #filter is an instance of something without a __call__
            #attribute.
            raise TypeError('filter')

    def register_filter(self, name, jinja_filter):
        """
        Register a filter.
        A filter is a function that accepts and acts on one string.
        The filters are accessible within the Jinja templating engine.

        Parameters
        ----------
        name : str
            name to give the filter in the Jinja engine
        filter : filter
        """
        return self._register_filter(self.environment, name, jinja_filter)

    def default_filters(self):
        """Override in subclasses to provide extra filters.

        This should return an iterable of 2-tuples: (name, class-or-function).
        You should call the method on the parent class and include the filters
        it provides.

        If a name is repeated, the last filter provided wins. Filters from
        user-supplied config win over filters provided by classes.
        """
        return default_filters.items()

    def _create_environment(self):
        """
        Create the Jinja templating environment.
        """
        here = os.path.dirname(os.path.realpath(__file__))

        paths = self.template_path + \
            [os.path.join(here, self.default_template_path),
             os.path.join(here, self.template_skeleton_path)]

        loaders = self.extra_loaders + [
            ExtensionTolerantLoader(FileSystemLoader(paths), self.template_extension),
            DictLoader({self._raw_template_key: self.raw_template})
        ]
        environment = Environment(
            loader=ChoiceLoader(loaders),
            extensions=JINJA_EXTENSIONS
            )

        environment.globals['uuid4'] = uuid.uuid4

        # Add default filters to the Jinja2 environment
        for key, value in self.default_filters():
            self._register_filter(environment, key, value)

        # Load user filters.  Overwrite existing filters if need be.
        if self.filters:
            for key, user_filter in self.filters.items():
                self._register_filter(environment, key, user_filter)

        return environment

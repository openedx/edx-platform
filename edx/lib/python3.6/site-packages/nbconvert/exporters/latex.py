"""LaTeX Exporter class"""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import os

from traitlets import Unicode, default
from traitlets.config import Config

from nbconvert.filters.highlight import Highlight2Latex
from nbconvert.filters.filter_links import resolve_references
from .templateexporter import TemplateExporter

class LatexExporter(TemplateExporter):
    """
    Exports to a Latex template.  Inherit from this class if your template is
    LaTeX based and you need custom tranformers/filters.  Inherit from it if 
    you are writing your own HTML template and need custom tranformers/filters.  
    If you don't need custom tranformers/filters, just change the 
    'template_file' config option.  Place your template in the special "/latex" 
    subfolder of the "../templates" folder.
    """
    export_from_notebook = "latex"

    @default('file_extension')
    def _file_extension_default(self):
        return '.tex'

    @default('template_file')
    def _template_file_default(self):
        return 'article.tplx'

    # Latex constants
    @default('default_template_path')
    def _default_template_path_default(self):
        return os.path.join("..", "templates", "latex")

    @default('template_skeleton_path')
    def _template_skeleton_path_default(self):
        return os.path.join("..", "templates", "latex", "skeleton")
    
    #Extension that the template files use.
    template_extension = Unicode(".tplx").tag(config=True)

    output_mimetype = 'text/latex'

    def default_filters(self):
        for x in super(LatexExporter, self).default_filters():
            yield x 
        yield ('resolve_references', resolve_references)

    @property
    def default_config(self):
        c = Config({
            'NbConvertBase': {
                'display_data_priority' : ['text/latex', 'application/pdf', 'image/png', 'image/jpeg', 'image/svg+xml', 'text/markdown', 'text/plain']
                },
             'ExtractOutputPreprocessor': {
                    'enabled':True
                 },
             'SVG2PDFPreprocessor': {
                    'enabled':True
                 },
             'LatexPreprocessor': {
                    'enabled':True
                 },
             'SphinxPreprocessor': {
                    'enabled':True
                 },
             'HighlightMagicsPreprocessor': {
                    'enabled':True
                 }
         })
        c.merge(super(LatexExporter,self).default_config)
        return c

    def from_notebook_node(self, nb, resources=None, **kw):
        langinfo = nb.metadata.get('language_info', {})
        lexer = langinfo.get('pygments_lexer', langinfo.get('name', None))
        self.register_filter('highlight_code',
                             Highlight2Latex(pygments_lexer=lexer, parent=self))
        return super(LatexExporter, self).from_notebook_node(nb, resources, **kw)

    def _create_environment(self):
        environment = super(LatexExporter, self)._create_environment()

        # Set special Jinja2 syntax that will not conflict with latex.
        environment.block_start_string = "((*"
        environment.block_end_string = "*))"
        environment.variable_start_string = "((("
        environment.variable_end_string = ")))"
        environment.comment_start_string = "((="
        environment.comment_end_string = "=))"

        return environment

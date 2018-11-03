"""reStructuredText Exporter class"""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from traitlets import default
from traitlets.config import Config

from .templateexporter import TemplateExporter


class RSTExporter(TemplateExporter):
    """
    Exports reStructuredText documents.
    """
    
    @default('file_extension')
    def _file_extension_default(self):
        return '.rst'

    @default('template_file')
    def _template_file_default(self):
        return 'rst.tpl'

    output_mimetype = 'text/restructuredtext'
    export_from_notebook = "rst"

    @property
    def default_config(self):
        c = Config({
            'ExtractOutputPreprocessor':{
                'enabled':True
                },
            'HighlightMagicsPreprocessor': {
                'enabled':True
                },
            })
        c.merge(super(RSTExporter,self).default_config)
        return c

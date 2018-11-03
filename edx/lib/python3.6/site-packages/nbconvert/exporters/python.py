"""Python script Exporter class"""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from traitlets import default

from .templateexporter import TemplateExporter


class PythonExporter(TemplateExporter):
    """
    Exports a Python code file.
    """
    @default('file_extension')
    def _file_extension_default(self):
        return '.py'

    @default('template_file')
    def _template_file_default(self):
        return 'python.tpl'

    output_mimetype = 'text/x-python'
    export_from_notebook = "python"

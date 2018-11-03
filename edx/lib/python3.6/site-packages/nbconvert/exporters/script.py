"""Generic script exporter class for any kernel language"""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import entrypoints
from .templateexporter import TemplateExporter

from traitlets import Dict, default
from .base import get_exporter


class ScriptExporter(TemplateExporter):
    # Caches of already looked-up and instantiated exporters for delegation:
    _exporters = Dict()
    _lang_exporters = Dict()
    export_form_notebook = "script"
    
    @default('template_file')
    def _template_file_default(self):
        return 'script.tpl'

    def _get_language_exporter(self, lang_name):
        """Find an exporter for the language name from notebook metadata.

        Uses the nbconvert.exporters.script group of entry points.
        Returns None if no exporter is found.
        """
        if lang_name not in self._lang_exporters:
            try:
                Exporter = entrypoints.get_single(
                    'nbconvert.exporters.script', lang_name).load()
            except entrypoints.NoSuchEntryPoint:
                self._lang_exporters[lang_name] = None
            else:
                self._lang_exporters[lang_name] = Exporter(parent=self)
        return self._lang_exporters[lang_name]

    def from_notebook_node(self, nb, resources=None, **kw):
        langinfo = nb.metadata.get('language_info', {})
        
        # delegate to custom exporter, if specified
        exporter_name = langinfo.get('nbconvert_exporter')
        if exporter_name and exporter_name != 'script':
            self.log.debug("Loading script exporter: %s", exporter_name)
            if exporter_name not in self._exporters:
                Exporter = get_exporter(exporter_name)
                self._exporters[exporter_name] = Exporter(parent=self)
            exporter = self._exporters[exporter_name]
            return exporter.from_notebook_node(nb, resources, **kw)

        # Look up a script exporter for this notebook's language
        lang_name = langinfo.get('name')
        if lang_name:
            self.log.debug("Using script exporter for language: %s", lang_name)
            exporter = self._get_language_exporter(lang_name)
            if exporter is not None:
                return exporter.from_notebook_node(nb, resources, **kw)

        # Fall back to plain script export
        self.file_extension = langinfo.get('file_extension', '.txt')
        self.output_mimetype = langinfo.get('mimetype', 'text/plain')
        return super(ScriptExporter, self).from_notebook_node(nb, resources, **kw)

"""Deprecated as of 5.0. Module containing hard-coded exporting functions."""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import warnings

from .base import (export, get_exporter, 
                   get_export_names , ExporterNameError)

from .exporter import Exporter
from .templateexporter import TemplateExporter
from .html import HTMLExporter
from .slides import SlidesExporter
from .latex import LatexExporter
from .pdf import PDFExporter
from .markdown import MarkdownExporter
from .python import PythonExporter
from .rst import RSTExporter
from .notebook import NotebookExporter
from .script import ScriptExporter

#-----------------------------------------------------------------------------
# Functions
#-----------------------------------------------------------------------------

warnings.warn("""`nbconvert.exporters.exporter_locator` is deprecated in favor of `nbconvert.exporters.base` since nbconvert 5.0.""",
    DeprecationWarning)

__all__ = [
    'export',
    'export_by_name',
    'get_exporter',
    'get_export_names',
    'ExporterNameError',
    'exporter_map',
]

exporter_map = dict(
    custom=TemplateExporter,
    html=HTMLExporter,
    slides=SlidesExporter,
    latex=LatexExporter,
    pdf=PDFExporter,
    markdown=MarkdownExporter,
    python=PythonExporter,
    rst=RSTExporter,
    notebook=NotebookExporter,
    script=ScriptExporter,
)

def _make_exporter(name, E):
    """make an export_foo function from a short key and Exporter class E"""
    def _export(nb, **kw):
        return export(E, nb, **kw)
    _export.__doc__ = """DEPRECATED: Export a notebook object to {0} format""".format(name)
    return _export
    
g = globals()

# These specific functions are deprecated as of 5.0
for name, E in exporter_map.items():
    g['export_%s' % name] = _make_exporter(name, E)
    __all__.append('export_%s' % name)


def export_by_name(format_name, nb, **kw):
    """
    Deprecated since version 5.0. 

    Export a notebook object to a template type by its name.  Reflection
    (Inspect) is used to find the template's corresponding explicit export
    method defined in this module.  That method is then called directly.
    
    Parameters
    ----------
    format_name : str
        Name of the template style to export to.
    """
    
    warnings.warn("export_by_name is deprecated since nbconvert 5.0. Instead, use export(get_exporter(format_name), nb, **kw)).", DeprecationWarning, stacklevel=2)

    try:
        Exporter = get_exporter(format_name) 
        return export(Exporter, nb, **kw)
    except ValueError:
        raise ExporterNameError("Exporter for `%s` not found" % format_name)

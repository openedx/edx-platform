"""Module that pre-processes the notebook for export to HTML.
"""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import os
import io
import hashlib
import nbconvert.resources

from traitlets import Unicode
from .base import Preprocessor


try:
    from notebook import DEFAULT_STATIC_FILES_PATH
except ImportError:
    DEFAULT_STATIC_FILES_PATH = None


class CSSHTMLHeaderPreprocessor(Preprocessor):
    """
    Preprocessor used to pre-process notebook for HTML output.  Adds IPython notebook
    front-end CSS and Pygments CSS to HTML output.
    """
    highlight_class = Unicode('.highlight',
                              help="CSS highlight class identifier"
    ).tag(config=True)

    def __init__(self, *pargs, **kwargs):
        Preprocessor.__init__(self, *pargs, **kwargs)
        self._default_css_hash = None

    def preprocess(self, nb, resources):
        """Fetch and add CSS to the resource dictionary

        Fetch CSS from IPython and Pygments to add at the beginning
        of the html files.  Add this css in resources in the 
        "inlining.css" key
        
        Parameters
        ----------
        nb : NotebookNode
            Notebook being converted
        resources : dictionary
            Additional resources used in the conversion process.  Allows
            preprocessors to pass variables into the Jinja engine.
        """
        resources['inlining'] = {}
        resources['inlining']['css'] = self._generate_header(resources)
        return nb, resources

    def _generate_header(self, resources):
        """ 
        Fills self.header with lines of CSS extracted from IPython 
        and Pygments.
        """
        from pygments.formatters import HtmlFormatter
        header = []
        
        # Construct path to Jupyter CSS
        sheet_filename = os.path.join(
            os.path.dirname(nbconvert.resources.__file__),
            'style.min.css',
        )
        
        # Load style CSS file.
        with io.open(sheet_filename, encoding='utf-8') as f:
            header.append(f.read())

        # Add pygments CSS
        formatter = HtmlFormatter()
        pygments_css = formatter.get_style_defs(self.highlight_class)
        header.append(pygments_css)

        # These ANSI CSS definitions will be part of style.min.css with the
        # Notebook release 5.0 and shall be removed afterwards!
        # See https://github.com/jupyter/nbconvert/pull/259
        header.append("""
/* Temporary definitions which will become obsolete with Notebook release 5.0 */
.ansi-black-fg { color: #3E424D; }
.ansi-black-bg { background-color: #3E424D; }
.ansi-black-intense-fg { color: #282C36; }
.ansi-black-intense-bg { background-color: #282C36; }
.ansi-red-fg { color: #E75C58; }
.ansi-red-bg { background-color: #E75C58; }
.ansi-red-intense-fg { color: #B22B31; }
.ansi-red-intense-bg { background-color: #B22B31; }
.ansi-green-fg { color: #00A250; }
.ansi-green-bg { background-color: #00A250; }
.ansi-green-intense-fg { color: #007427; }
.ansi-green-intense-bg { background-color: #007427; }
.ansi-yellow-fg { color: #DDB62B; }
.ansi-yellow-bg { background-color: #DDB62B; }
.ansi-yellow-intense-fg { color: #B27D12; }
.ansi-yellow-intense-bg { background-color: #B27D12; }
.ansi-blue-fg { color: #208FFB; }
.ansi-blue-bg { background-color: #208FFB; }
.ansi-blue-intense-fg { color: #0065CA; }
.ansi-blue-intense-bg { background-color: #0065CA; }
.ansi-magenta-fg { color: #D160C4; }
.ansi-magenta-bg { background-color: #D160C4; }
.ansi-magenta-intense-fg { color: #A03196; }
.ansi-magenta-intense-bg { background-color: #A03196; }
.ansi-cyan-fg { color: #60C6C8; }
.ansi-cyan-bg { background-color: #60C6C8; }
.ansi-cyan-intense-fg { color: #258F8F; }
.ansi-cyan-intense-bg { background-color: #258F8F; }
.ansi-white-fg { color: #C5C1B4; }
.ansi-white-bg { background-color: #C5C1B4; }
.ansi-white-intense-fg { color: #A1A6B2; }
.ansi-white-intense-bg { background-color: #A1A6B2; }

.ansi-bold { font-weight: bold; }
""")

        # Load the user's custom CSS and IPython's default custom CSS.  If they
        # differ, assume the user has made modifications to his/her custom CSS
        # and that we should inline it in the nbconvert output.
        config_dir = resources['config_dir']
        custom_css_filename = os.path.join(config_dir, 'custom', 'custom.css')
        if os.path.isfile(custom_css_filename):
            if DEFAULT_STATIC_FILES_PATH and self._default_css_hash is None:
                self._default_css_hash = self._hash(os.path.join(DEFAULT_STATIC_FILES_PATH, 'custom', 'custom.css'))
            if self._hash(custom_css_filename) != self._default_css_hash:
                with io.open(custom_css_filename, encoding='utf-8') as f:
                    header.append(f.read())
        return header

    def _hash(self, filename):
        """Compute the hash of a file."""
        md5 = hashlib.md5()
        with open(filename, 'rb') as f:
            md5.update(f.read())
        return md5.digest()

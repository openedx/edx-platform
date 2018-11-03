"""Module containing a preprocessor that converts outputs in the notebook from 
one format to another.
"""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import base64
import io
import os
import sys
import subprocess

from ipython_genutils.py3compat import cast_unicode_py2
from testpath.tempdir import TemporaryDirectory
from traitlets import Unicode, default

from .convertfigures import ConvertFiguresPreprocessor


INKSCAPE_APP = '/Applications/Inkscape.app/Contents/Resources/bin/inkscape'

if sys.platform == "win32":
    try:
        import winreg
    except ImportError:
        import _winreg as winreg


class SVG2PDFPreprocessor(ConvertFiguresPreprocessor):
    """
    Converts all of the outputs in a notebook from SVG to PDF.
    """

    @default('from_format')
    def _from_format_default(self):
        return 'image/svg+xml'

    @default('to_format')
    def _to_format_default(self):
        return 'application/pdf'

    command = Unicode(
        help="""The command to use for converting SVG to PDF
        
        This string is a template, which will be formatted with the keys
        to_filename and from_filename.
        
        The conversion call must read the SVG from {from_flename},
        and write a PDF to {to_filename}.
        """).tag(config=True)

    @default('command')
    def _command_default(self):
        return self.inkscape + \
               ' --without-gui --export-pdf="{to_filename}" "{from_filename}"'
    
    inkscape = Unicode(help="The path to Inkscape, if necessary").tag(config=True)
    @default('inkscape')
    def _inkscape_default(self):
        if sys.platform == "darwin":
            if os.path.isfile(INKSCAPE_APP):
                return INKSCAPE_APP
        if sys.platform == "win32":
            wr_handle = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
            try:
                rkey = winreg.OpenKey(wr_handle, "SOFTWARE\\Classes\\inkscape.svg\\DefaultIcon")
                inkscape = winreg.QueryValueEx(rkey, "")[0]
            except FileNotFoundError:
                raise FileNotFoundError("Inkscape executable not found")
            return inkscape
        return "inkscape"


    def convert_figure(self, data_format, data):
        """
        Convert a single SVG figure to PDF.  Returns converted data.
        """

        #Work in a temporary directory
        with TemporaryDirectory() as tmpdir:
            
            #Write fig to temp file
            input_filename = os.path.join(tmpdir, 'figure.svg')
            # SVG data is unicode text
            with io.open(input_filename, 'w', encoding='utf8') as f:
                f.write(cast_unicode_py2(data))

            #Call conversion application
            output_filename = os.path.join(tmpdir, 'figure.pdf')
            shell = self.command.format(from_filename=input_filename, 
                                   to_filename=output_filename)
            subprocess.call(shell, shell=True) #Shell=True okay since input is trusted.

            #Read output from drive
            # return value expects a filename
            if os.path.isfile(output_filename):
                with open(output_filename, 'rb') as f:
                    # PDF is a nb supported binary, data type, so base64 encode.
                    return base64.encodestring(f.read())
            else:
                raise TypeError("Inkscape svg to pdf conversion failed")

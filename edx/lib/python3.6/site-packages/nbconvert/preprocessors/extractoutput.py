"""A preprocessor that extracts all of the outputs from the
notebook file.  The extracted outputs are returned in the 'resources' dictionary.
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from binascii import a2b_base64
import sys
import os
import json
from mimetypes import guess_extension

from traitlets import Unicode, Set
from .base import Preprocessor

if sys.version_info < (3,):
    text_type = basestring
else:
    text_type = str


def guess_extension_without_jpe(mimetype):
    """
    This function fixes a problem with '.jpe' extensions
    of jpeg images which are then not recognised by latex.
    For any other case, the function works in the same way
    as mimetypes.guess_extension
    """
    ext = guess_extension(mimetype)
    if ext==".jpe":
        ext=".jpeg"
    return ext

class ExtractOutputPreprocessor(Preprocessor):
    """
    Extracts all of the outputs from the notebook file.  The extracted 
    outputs are returned in the 'resources' dictionary.
    """

    output_filename_template = Unicode(
        "{unique_key}_{cell_index}_{index}{extension}"
    ).tag(config=True)

    extract_output_types = Set(
        {'image/png', 'image/jpeg', 'image/svg+xml', 'application/pdf'}
    ).tag(config=True)

    def preprocess_cell(self, cell, resources, cell_index):
        """
        Apply a transformation on each cell,
        
        Parameters
        ----------
        cell : NotebookNode cell
            Notebook cell being processed
        resources : dictionary
            Additional resources used in the conversion process.  Allows
            preprocessors to pass variables into the Jinja engine.
        cell_index : int
            Index of the cell being processed (see base.py)
        """

        #Get the unique key from the resource dict if it exists.  If it does not 
        #exist, use 'output' as the default.  Also, get files directory if it
        #has been specified
        unique_key = resources.get('unique_key', 'output')
        output_files_dir = resources.get('output_files_dir', None)
        
        #Make sure outputs key exists
        if not isinstance(resources['outputs'], dict):
            resources['outputs'] = {}
            
        #Loop through all of the outputs in the cell
        for index, out in enumerate(cell.get('outputs', [])):
            if out.output_type not in {'display_data', 'execute_result'}:
                continue
            #Get the output in data formats that the template needs extracted
            for mime_type in self.extract_output_types:
                if mime_type in out.data:
                    data = out.data[mime_type]

                    if (
                        not isinstance(data, text_type)
                        or mime_type == 'application/json'
                    ):
                        # Data is either JSON-like and was parsed into a Python
                        # object according to the spec, or data is for sure
                        # JSON. In the latter case we want to go extra sure that
                        # we enclose a scalar string value into extra quotes by
                        # serializing it properly.
                        data = json.dumps(data)

                    #Binary files are base64-encoded, SVG is already XML
                    if mime_type in {'image/png', 'image/jpeg', 'application/pdf'}:
                        # data is b64-encoded as text (str, unicode),
                        # we want the original bytes
                        data = a2b_base64(data)
                    elif sys.platform == 'win32':
                        data = data.replace('\n', '\r\n').encode("UTF-8")
                    else:
                        data = data.encode("UTF-8")
                    
                    ext = guess_extension_without_jpe(mime_type)
                    if ext is None:
                        ext = '.' + mime_type.rsplit('/')[-1]
                    if out.metadata.get('filename', ''):
                        filename = out.metadata['filename']
                        if not filename.endswith(ext):
                            filename+=ext
                    else:
                        filename = self.output_filename_template.format(
                                    unique_key=unique_key,
                                    cell_index=cell_index,
                                    index=index,
                                    extension=ext)

                    # On the cell, make the figure available via
                    #   cell.outputs[i].metadata.filenames['mime/type']
                    # where
                    #   cell.outputs[i].data['mime/type'] contains the data
                    if output_files_dir is not None:
                        filename = os.path.join(output_files_dir, filename)
                    out.metadata.setdefault('filenames', {})
                    out.metadata['filenames'][mime_type] = filename

                    if filename in resources['outputs']:
                        raise ValueError(
                            "Your outputs have filename metadata associated "
                            "with them. Nbconvert saves these outputs to "
                            "external files using this filename metadata. "
                            "Filenames need to be unique across the notebook, "
                            "or images will be overwritten. The filename {} is "
                            "associated with more than one output. The second "
                            "output associated with this filename is in cell "
                            "{}.".format(filename, cell_index)
                            )
                    #In the resources, make the figure available via
                    #   resources['outputs']['filename'] = data
                    resources['outputs'][filename] = data

        return cell, resources

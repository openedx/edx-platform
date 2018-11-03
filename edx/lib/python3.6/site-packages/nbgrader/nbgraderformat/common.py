import json
import os
import jsonschema

from jsonschema import ValidationError
from traitlets.config import LoggingConfigurable


root = os.path.dirname(__file__)

class BaseValidator(LoggingConfigurable):

    schema = None

    def __init__(self, version):
        if self.schema is None:
            with open(os.path.join(root, "v{:d}.json".format(version)), "r") as fh:
                self.schema = json.loads(fh.read())

    def upgrade_notebook_metadata(self, nb):
        for cell in nb.cells:
            self.upgrade_cell_metadata(cell)
        return nb

    def upgrade_cell_metadata(self, cell):
        raise NotImplementedError("this method must be implemented by subclasses")

    def validate_cell(self, cell):
        if 'nbgrader' not in cell.metadata:
            return
        jsonschema.validate(cell.metadata['nbgrader'], self.schema)

    def validate_nb(self, nb):
        for cell in nb.cells:
            self.validate_cell(cell)

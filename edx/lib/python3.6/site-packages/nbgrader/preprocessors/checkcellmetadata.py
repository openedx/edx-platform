import traceback

from ..nbgraderformat import Validator, ValidationError
from . import NbGraderPreprocessor

class CheckCellMetadata(NbGraderPreprocessor):
    """A preprocessor for checking that grade ids are unique."""

    def preprocess(self, nb, resources):
        try:
            Validator().validate_nb(nb)
        except ValidationError:
            self.log.error(traceback.format_exc())
            msg = "Notebook failed to validate. Please update the metadata with `nbgrader update`."
            self.log.error(msg)
            raise ValidationError(msg)

        return nb, resources

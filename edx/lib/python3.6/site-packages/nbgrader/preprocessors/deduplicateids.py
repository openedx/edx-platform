from .. import utils
from . import NbGraderPreprocessor

class DeduplicateIds(NbGraderPreprocessor):
    """A preprocessor to overwrite information about grade and solution cells."""

    def preprocess(self, nb, resources):
        # keep track of grade ids encountered so far
        self.grade_ids = set([])

        # reverse cell order
        nb.cells = nb.cells[::-1]

        # process each cell in reverse order
        nb, resources = super(DeduplicateIds, self).preprocess(nb, resources)

        # unreverse cell order
        nb.cells = nb.cells[::-1]

        return nb, resources

    def preprocess_cell(self, cell, resources, cell_index):
        if not (utils.is_grade(cell) or utils.is_solution(cell) or utils.is_locked(cell)):
            return cell, resources

        grade_id = cell.metadata.nbgrader['grade_id']
        if grade_id in self.grade_ids:
            self.log.warning("Cell with id '%s' exists multiple times!", grade_id)
            cell.metadata.nbgrader = {}
        else:
            self.grade_ids.add(grade_id)

        return cell, resources

from .. import utils
from ..api import Gradebook
from . import NbGraderPreprocessor


class SaveAutoGrades(NbGraderPreprocessor):
    """Preprocessor for saving out the autograder grades into a database"""

    def preprocess(self, nb, resources):
        # pull information from the resources
        self.notebook_id = resources['nbgrader']['notebook']
        self.assignment_id = resources['nbgrader']['assignment']
        self.student_id = resources['nbgrader']['student']
        self.db_url = resources['nbgrader']['db_url']

        # connect to the database
        self.gradebook = Gradebook(self.db_url)

        with self.gradebook:
            # process the cells
            nb, resources = super(SaveAutoGrades, self).preprocess(nb, resources)

        return nb, resources

    def _add_score(self, cell, resources):
        """Graders can override the autograder grades, and may need to
        manually grade written solutions anyway. This function adds
        score information to the database if it doesn't exist. It does
        NOT override the 'score' field, as this is the manual score
        that might have been provided by a grader.

        """
        # these are the fields by which we will identify the score
        # information
        grade = self.gradebook.find_grade(
            cell.metadata['nbgrader']['grade_id'],
            self.notebook_id,
            self.assignment_id,
            self.student_id)

        # determine what the grade is
        auto_score, _ = utils.determine_grade(cell)
        grade.auto_score = auto_score

        # if there was previously a manual grade, or if there is no autograder
        # score, then we should mark this as needing review
        if (grade.manual_score is not None) or (grade.auto_score is None):
            grade.needs_manual_grade = True
        else:
            grade.needs_manual_grade = False

        self.gradebook.db.commit()
        self.log.debug(grade)

    def _add_comment(self, cell, resources):
        comment = self.gradebook.find_comment(
            cell.metadata['nbgrader']['grade_id'],
            self.notebook_id,
            self.assignment_id,
            self.student_id)

        if cell.metadata.nbgrader.get("checksum", None) == utils.compute_checksum(cell):
            comment.auto_comment = "No response."
        else:
            comment.auto_comment = None

        self.gradebook.db.commit()
        self.log.debug(comment)

    def preprocess_cell(self, cell, resources, cell_index):
        # if it's a grade cell, the add a grade
        if utils.is_grade(cell):
            self._add_score(cell, resources)

        if utils.is_solution(cell):
            self._add_comment(cell, resources)

        return cell, resources

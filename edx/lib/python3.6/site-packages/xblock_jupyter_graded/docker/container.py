import json
import os
import shutil
from subprocess import Popen, PIPE

from nbgrader.api import Gradebook
import nbformat

from autograded_checkers import ModuleNotFoundChecker
from exceptions import ValidationError, ContainerError

COURSE_ROOT = "/home/nbgrader/course"
GRADEBOOK_NAME = "gradebook.db"


class BaseContainer(object):
    def __init__(self, root_dir):
        self.root = root_dir
        self.db_path = "sqlite:///{}".format(os.path.join(root_dir, GRADEBOOK_NAME))

        # Hardcoding b/c we don't really care what these are since this is
        # a disposable container
        self.course_id = "course"
        self.pset_id = "ps1"

    def _get_notebook_api(nb_id):
        """Return NbGraderAPI instance configured for course and notebook

        NOTE: Not currently used. Only necessary for high level API. Here in
        case we ever move to using that. Can do more config here."""
        config = Config()
        config.Exchange.course_id = "course"
        config.Exchange.root = "/tmp/nbgrader/exchange"
        config.CourseDirectory.root = self.root
        config.CourseDirectory.db_url = self.db_path
        config.CourseDirectory.notebook_id = os.path.splitext(nb_id)[0]
        config.ExecutePreprocessor.kernel_name= 'python3'

        api = NbGraderAPI(config=config)
        return api

    def check_result(self, results):
        """Raises DBManagerError if error exists in `result_dict`
        
        Translates specific error types into something more readable"""
        if 'NotJSONError' in results:
            raise ValidationError("Notebook does not appear to be valid JSON")

        raise ContainerError(results)


class AssignContainer(BaseContainer):
    def __init__(self, nb_filename, root_dir=COURSE_ROOT):
        super().__init__(root_dir)
        self.nb_filename = nb_filename

    def get_instructor_nb(self):
        """Return path to instructor notebook
        
        Currently hardcoded since it is mapped to the container.

        Could be overridden to fetch notebook from some location
        """
        return os.path.join(self.root, "source", self.pset_id, self.nb_filename)

    def generate_results(self, success, err=None, max_score=None):
        """Generate a result content"""
        err_str = err
        if type(err) == bytes:
            err_str = err.decode('utf-8')

        results = {
            'success': success,
            'err': err_str,
            'max_score': max_score
        }

        return results

    def return_results(self, results):
        """Writes result to released directory"""
        # Generate results filepath
        nb_filename = os.path.splitext(self.nb_filename)[0]
        result_filename = "{}_results.json".format(nb_filename)
        result_path = os.path.join(self.root, "release", self.pset_id,
            result_filename)

        # Write out result json
        with open(result_path, 'w') as f:
            json.dump(results, f)

    def return_student_version(self):
        """Do what's necessary to return student version from container
        
        Default implementation returns student version automatically because 
        assign generates the file in /home/course/release/unit/ and that dir
        is mapped back to the release directory in EdX
        """
        pass

    def get_max_nb_score(self):
        """Return the max code score from the gradebook"""
        nb_name = os.path.splitext(self.nb_filename)[0]
        with Gradebook(self.db_path) as gb:
            nb = gb.find_notebook(nb_name, self.pset_id)
            max_score = nb.max_code_score
        return max_score

    def generate_student_version(self, nb_path):
        """Runs nbgrader assign to generate student version of notebook"""
        args = [
            'nbgrader', 'assign',
            '--create', '--force',
            '--course-dir', self.root,
            '--db', self.db_path,
            '--assignment', self.pset_id,
            '--notebook', os.path.splitext(self.nb_filename)[0],
        ]
        p = Popen(args, stderr=PIPE, stdout=PIPE)
        out, err = p.communicate()

        if p.returncode != 0:
            self.check_result(err.decode('utf-8'))

        return out, err

    def run(self):
        inst_nb_path = self.get_instructor_nb()

        try:
            out, err = self.generate_student_version(inst_nb_path)
            max_score = self.get_max_nb_score()
            results = self.generate_results(success=True, max_score=max_score)
            self.return_student_version()
        except Exception as e:
            results = self.generate_results(False, err=str(e))

        self.return_results(results)
        return results


class AutoGradeContainer(BaseContainer):
    def __init__(self, nb_filename, username, gen_feedback, 
            autograded_checkers=[], root_dir=COURSE_ROOT):
        super().__init__(root_dir)
        self.autograded_checkers = autograded_checkers
        self.nb_filename = nb_filename
        self.username = username
        self.gen_feedback = gen_feedback

    def get_student_nb(self):
        """Return path to student notebook
        
        Currently hardcoded since it is mapped to the container.

        Could be overridden to fetch notebook from some location
        """
        return os.path.join(self.root, "submitted", self.username, 
            self.pset_id, self.nb_filename)

    def generate_results(self, success, autograded_err=None, err=None, 
            total_score=None, section_scores=None):
        """Generate a result content"""
        err_str = err
        if type(err) == bytes:
            err_str = err.decode('utf-8')

        results = {
            'success': success,
            'err': err_str,
            'autograded_err': autograded_err,
            'total_score': total_score,
            'section_scores': section_scores,
        }

        return results

    def return_results(self, results):
        """Writes result json to mapped autograded directory
        
        This file contains execution meta-data you want returned to edx
        (eg, scores, err text, container run status, etc)

        Could be implemented to return results some other way
        """

        # Generate results filepath
        nb_filename = os.path.splitext(self.nb_filename)[0]
        result_filename = "{}_results.json".format(nb_filename)
        result_path = os.path.join("/autograded", result_filename)

        # Write out result json
        with open(result_path, 'w') as f:
            json.dump(results, f)

    def return_autograded_version(self):
        """Writes autograded version to mapped path
        
        Could be implemented to return results some other way
        """
        src = os.path.join(self.root, "autograded", self.username, 
            self.pset_id, self.nb_filename)
        dst = os.path.join("/autograded", self.nb_filename)
        shutil.copyfile(src, dst)

    def return_feedback(self):
        """Writes feedback html to mapped path

        Could be implemented to return results some other way
        """
        fb_filename = "{}.html".format(os.path.splitext(self.nb_filename)[0])
        src = os.path.join(self.root, "feedback", self.username, 
            self.pset_id, fb_filename)
        dst = os.path.join("/feedback", fb_filename)
        shutil.copyfile(src, dst)

    def get_total_score(self):
        """Return total student score for notebook"""
        nb_name = os.path.splitext(self.nb_filename)[0]
        with Gradebook(self.db_path) as gb:
            nb = gb.find_submission_notebook(nb_name, self.pset_id, self.username)
            score = nb.code_score
        return score

    def get_section_scores(self):
        """Return student score for each problem in notebook"""
        grades = []
        nb_name = os.path.splitext(self.nb_filename)[0]
        with Gradebook(self.db_path) as gb:
            nb = gb.find_submission_notebook(nb_name, self.pset_id, self.username)
            for problem in nb.grades:
                grades.append(problem.to_dict())
        return grades

    def autograde(self):
        """Run `nbgrader autograde` to autograde student notebook"""
        args = [
            'nbgrader', 'autograde',
            '--create', '--force',
            '--student', self.username,
            '--course-dir', self.root,
            '--db', self.db_path,
            '--assignment', self.pset_id,
            '--notebook', os.path.splitext(self.nb_filename)[0],
        ]
        p = Popen(args, stderr=PIPE, stdout=PIPE)
        out, err = p.communicate()

        if p.returncode != 0:
            self.check_result(err.decode('utf-8'))

        return out, err

    def generate_feedback_html(self):
        """Runs `nbgrader feedback` to generate html of student feedback"""
        args = [
            'nbgrader', 'feedback',
            '--force',
            '--student', self.username,
            '--course-dir', self.root,
            '--db', self.db_path,
            '--assignment', self.pset_id,
            '--notebook', os.path.splitext(self.nb_filename)[0],
        ]
        p = Popen(args, stderr=PIPE, stdout=PIPE)
        out, err = p.communicate()

        # TODO: Add some better error handling in here
        if p.returncode != 0:
            raise ContainerError(err.decode('utf-8'))

        return out, err

    def run(self):
        student_nb_path = self.get_student_nb()

        try:
            out, err = self.autograde()
            total_score = self.get_total_score()
            section_scores = self.get_section_scores()
            autograded_err = self.run_autograded_nb_checks()
            results = self.generate_results(
                    success=True, 
                    err=err,
                    autograded_err=autograded_err,
                    total_score=total_score,
                    section_scores=section_scores,
            )
            self.return_autograded_version()

            if self.gen_feedback:
                fb_out, fb_err = self.generate_feedback_html()
                self.return_feedback()

        except Exception as e:
            print(e)
            results = self.generate_results(False, err=str(e))

        self.return_results(results)
        return results

    def run_autograded_nb_checks(self):
        """Returns first error from running all autograded_checkers"""
        if not self.autograded_checkers:
            print("No checkers - return None")
            return

        print("Running Checkers: {}".format(self.autograded_checkers))
        # Load autograded nb into dict
        nb_path = os.path.join(self.root, "autograded", self.username, 
            self.pset_id, self.nb_filename)
        nb = self._load_nb_to_dict(nb_path)

        cells = (cell for cell in nb['cells'])
        try:
            # Run checker on each cell
            for cell in cells:
                for checker in self.autograded_checkers:
                    checker.check_cell(cell)

            # Give last opporunity to raise ValidationError
            for checker in self.autograded_checkers:
                checker.finalize()

        except ValidationError as e:
            return str(e)

    def _load_nb_to_dict(self, nb_path):
        """Loads the students autograded notebook"""
        if os.path.exists(nb_path):
            with open(nb_path, 'r') as f:
                raw = f.read()

        # NOTE: as_version should be...?
        nb = nbformat.reads(raw, as_version=4)
        return nb




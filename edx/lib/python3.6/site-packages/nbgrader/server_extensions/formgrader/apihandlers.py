import json
import os

from tornado import web

from .base import BaseApiHandler, check_xsrf
from ...api import MissingEntry


class GradeCollectionHandler(BaseApiHandler):
    @web.authenticated
    @check_xsrf
    def get(self):
        submission_id = self.get_argument("submission_id")
        try:
            notebook = self.gradebook.find_submission_notebook_by_id(submission_id)
        except MissingEntry:
            raise web.HTTPError(404)
        self.write(json.dumps([g.to_dict() for g in notebook.grades]))


class CommentCollectionHandler(BaseApiHandler):
    @web.authenticated
    @check_xsrf
    def get(self):
        submission_id = self.get_argument("submission_id")
        try:
            notebook = self.gradebook.find_submission_notebook_by_id(submission_id)
        except MissingEntry:
            raise web.HTTPError(404)
        self.write(json.dumps([c.to_dict() for c in notebook.comments]))


class GradeHandler(BaseApiHandler):
    @web.authenticated
    @check_xsrf
    def get(self, grade_id):
        try:
            grade = self.gradebook.find_grade_by_id(grade_id)
        except MissingEntry:
            raise web.HTTPError(404)
        self.write(json.dumps(grade.to_dict()))

    @web.authenticated
    @check_xsrf
    def put(self, grade_id):
        try:
            grade = self.gradebook.find_grade_by_id(grade_id)
        except MissingEntry:
            raise web.HTTPError(404)

        data = self.get_json_body()
        grade.manual_score = data.get("manual_score", None)
        grade.extra_credit = data.get("extra_credit", None)
        if grade.manual_score is None and grade.auto_score is None:
            grade.needs_manual_grade = True
        else:
            grade.needs_manual_grade = False
        self.gradebook.db.commit()
        self.write(json.dumps(grade.to_dict()))


class CommentHandler(BaseApiHandler):
    @web.authenticated
    @check_xsrf
    def get(self, grade_id):
        try:
            comment = self.gradebook.find_comment_by_id(grade_id)
        except MissingEntry:
            raise web.HTTPError(404)
        self.write(json.dumps(comment.to_dict()))

    @web.authenticated
    @check_xsrf
    def put(self, grade_id):
        try:
            comment = self.gradebook.find_comment_by_id(grade_id)
        except MissingEntry:
            raise web.HTTPError(404)

        data = self.get_json_body()
        comment.manual_comment = data.get("manual_comment", None)
        self.gradebook.db.commit()
        self.write(json.dumps(comment.to_dict()))


class FlagSubmissionHandler(BaseApiHandler):
    @web.authenticated
    @check_xsrf
    def post(self, submission_id):
        try:
            submission = self.gradebook.find_submission_notebook_by_id(submission_id)
        except MissingEntry:
            raise web.HTTPError(404)

        submission.flagged = not submission.flagged
        self.gradebook.db.commit()
        self.write(json.dumps(submission.to_dict()))


class AssignmentCollectionHandler(BaseApiHandler):
    @web.authenticated
    @check_xsrf
    def get(self):
        assignments = self.api.get_assignments()
        self.write(json.dumps(assignments))


class AssignmentHandler(BaseApiHandler):
    @web.authenticated
    @check_xsrf
    def get(self, assignment_id):
        assignment = self.api.get_assignment(assignment_id)
        if assignment is None:
            raise web.HTTPError(404)
        self.write(json.dumps(assignment))

    @web.authenticated
    @check_xsrf
    def put(self, assignment_id):
        data = self.get_json_body()
        duedate = data.get("duedate_notimezone", None)
        timezone = data.get("duedate_timezone", None)
        if duedate and timezone:
            duedate = duedate + " " + timezone
        assignment = {"duedate": duedate}
        self.gradebook.update_or_create_assignment(assignment_id, **assignment)
        sourcedir = os.path.abspath(self.coursedir.format_path(self.coursedir.source_directory, '.', assignment_id))
        if not os.path.isdir(sourcedir):
            os.makedirs(sourcedir)
        self.write(json.dumps(self.api.get_assignment(assignment_id)))


class NotebookCollectionHandler(BaseApiHandler):
    @web.authenticated
    @check_xsrf
    def get(self, assignment_id):
        notebooks = self.api.get_notebooks(assignment_id)
        self.write(json.dumps(notebooks))


class SubmissionCollectionHandler(BaseApiHandler):
    @web.authenticated
    @check_xsrf
    def get(self, assignment_id):
        submissions = self.api.get_submissions(assignment_id)
        self.write(json.dumps(submissions))


class SubmissionHandler(BaseApiHandler):
    @web.authenticated
    @check_xsrf
    def get(self, assignment_id, student_id):
        submission = self.api.get_submission(assignment_id, student_id)
        if submission is None:
            raise web.HTTPError(404)
        self.write(json.dumps(submission))


class SubmittedNotebookCollectionHandler(BaseApiHandler):
    @web.authenticated
    @check_xsrf
    def get(self, assignment_id, notebook_id):
        submissions = self.api.get_notebook_submissions(assignment_id, notebook_id)
        self.write(json.dumps(submissions))


class StudentCollectionHandler(BaseApiHandler):
    @web.authenticated
    @check_xsrf
    def get(self):
        students = self.api.get_students()
        self.write(json.dumps(students))


class StudentHandler(BaseApiHandler):
    @web.authenticated
    @check_xsrf
    def get(self, student_id):
        student = self.api.get_student(student_id)
        if student is None:
            raise web.HTTPError(404)
        self.write(json.dumps(student))

    @web.authenticated
    @check_xsrf
    def put(self, student_id):
        data = self.get_json_body()
        student = {
            "last_name": data.get("last_name", None),
            "first_name": data.get("first_name", None),
            "email": data.get("email", None),
        }
        self.gradebook.update_or_create_student(student_id, **student)
        self.write(json.dumps(self.api.get_student(student_id)))


class StudentSubmissionCollectionHandler(BaseApiHandler):
    @web.authenticated
    @check_xsrf
    def get(self, student_id):
        submissions = self.api.get_student_submissions(student_id)
        self.write(json.dumps(submissions))


class StudentNotebookSubmissionCollectionHandler(BaseApiHandler):
    @web.authenticated
    @check_xsrf
    def get(self, student_id, assignment_id):
        submissions = self.api.get_student_notebook_submissions(student_id, assignment_id)
        self.write(json.dumps(submissions))


class AssignHandler(BaseApiHandler):
    @web.authenticated
    @check_xsrf
    def post(self, assignment_id):
        self.write(json.dumps(self.api.assign(assignment_id)))


class UnReleaseHandler(BaseApiHandler):
    @web.authenticated
    @check_xsrf
    def post(self, assignment_id):
        self.write(json.dumps(self.api.unrelease(assignment_id)))


class ReleaseHandler(BaseApiHandler):
    @web.authenticated
    @check_xsrf
    def post(self, assignment_id):
        self.write(json.dumps(self.api.release(assignment_id)))


class CollectHandler(BaseApiHandler):
    @web.authenticated
    @check_xsrf
    def post(self, assignment_id):
        self.write(json.dumps(self.api.collect(assignment_id)))


class AutogradeHandler(BaseApiHandler):
    @web.authenticated
    @check_xsrf
    def post(self, assignment_id, student_id):
        self.write(json.dumps(self.api.autograde(assignment_id, student_id)))


default_handlers = [
    (r"/formgrader/api/assignments", AssignmentCollectionHandler),
    (r"/formgrader/api/assignment/([^/]+)", AssignmentHandler),
    (r"/formgrader/api/assignment/([^/]+)/assign", AssignHandler),
    (r"/formgrader/api/assignment/([^/]+)/unrelease", UnReleaseHandler),
    (r"/formgrader/api/assignment/([^/]+)/release", ReleaseHandler),
    (r"/formgrader/api/assignment/([^/]+)/collect", CollectHandler),

    (r"/formgrader/api/notebooks/([^/]+)", NotebookCollectionHandler),

    (r"/formgrader/api/submissions/([^/]+)", SubmissionCollectionHandler),
    (r"/formgrader/api/submission/([^/]+)/([^/]+)", SubmissionHandler),
    (r"/formgrader/api/submission/([^/]+)/([^/]+)/autograde", AutogradeHandler),

    (r"/formgrader/api/submitted_notebooks/([^/]+)/([^/]+)", SubmittedNotebookCollectionHandler),
    (r"/formgrader/api/submitted_notebook/([^/]+)/flag", FlagSubmissionHandler),

    (r"/formgrader/api/grades", GradeCollectionHandler),
    (r"/formgrader/api/grade/([^/]+)", GradeHandler),

    (r"/formgrader/api/comments", CommentCollectionHandler),
    (r"/formgrader/api/comment/([^/]+)", CommentHandler),

    (r"/formgrader/api/students", StudentCollectionHandler),
    (r"/formgrader/api/student/([^/]+)", StudentHandler),

    (r"/formgrader/api/student_submissions/([^/]+)", StudentSubmissionCollectionHandler),
    (r"/formgrader/api/student_notebook_submissions/([^/]+)/([^/]+)", StudentNotebookSubmissionCollectionHandler),
]

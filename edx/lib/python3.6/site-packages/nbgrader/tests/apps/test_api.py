import pytest
import sys
import os

from os.path import join
from traitlets.config import Config
from datetime import datetime

from ...apps.api import NbGraderAPI
from ...coursedir import CourseDirectory
from ...utils import rmtree, get_username, parse_utc
from .. import run_nbgrader
from .base import BaseTestApp
from .conftest import notwindows, windows


@pytest.fixture
def api(request, course_dir, db, exchange):
    config = Config()
    config.Exchange.course_id = "abc101"
    config.Exchange.root = exchange
    config.CourseDirectory.root = course_dir
    config.CourseDirectory.db_url = db

    coursedir = CourseDirectory(config=config)
    api = NbGraderAPI(coursedir, config=config)

    return api


class TestNbGraderAPI(BaseTestApp):

    if sys.platform == 'win32':
        tz = "Coordinated Universal Time"
    else:
        tz = "UTC"

    def test_get_source_assignments(self, api, course_dir):
        assert api.get_source_assignments() == set([])

        self._empty_notebook(join(course_dir, "source", "ps1", "problem1.ipynb"))
        self._empty_notebook(join(course_dir, "source", "ps2", "problem1.ipynb"))
        self._make_file(join(course_dir, "source", "blah"))
        assert api.get_source_assignments() == {"ps1", "ps2"}

    @notwindows
    def test_get_released_assignments(self, api, exchange, course_dir):
        assert api.get_released_assignments() == set([])

        self._copy_file(join("files", "test.ipynb"), join(course_dir, "release", "ps1", "p1.ipynb"))
        run_nbgrader(["release", "ps1", "--course", "abc101", "--Exchange.root={}".format(exchange)])
        assert api.get_released_assignments() == {"ps1"}

        api.course_id = None
        assert api.get_released_assignments() == set([])

    @windows
    def test_get_released_assignments_windows(self, api, exchange, course_dir):
        assert api.get_released_assignments() == set([])

        api.course_id = 'abc101'
        assert api.get_released_assignments() == set([])

    def test_get_submitted_students(self, api, course_dir):
        assert api.get_submitted_students("ps1") == set([])

        self._empty_notebook(join(course_dir, "submitted", "foo", "ps1", "problem1.ipynb"))
        self._empty_notebook(join(course_dir, "submitted", "bar", "ps1", "problem1.ipynb"))
        self._make_file(join(course_dir, "submitted", "blah"))
        assert api.get_submitted_students("ps1") == {"foo", "bar"}
        assert api.get_submitted_students("*") == {"foo", "bar"}

    def test_get_submitted_timestamp(self, api, course_dir):
        assert api.get_submitted_timestamp("ps1", "foo") is None

        self._empty_notebook(join(course_dir, "submitted", "foo", "ps1", "problem1.ipynb"))
        assert api.get_submitted_timestamp("ps1", "foo") is None

        timestamp = datetime.now()
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "timestamp.txt"), contents=timestamp.isoformat())
        assert api.get_submitted_timestamp("ps1", "foo") == timestamp

    def test_get_autograded_students(self, api, course_dir, db):
        self._empty_notebook(join(course_dir, "source", "ps1", "problem1.ipynb"))
        run_nbgrader(["assign", "ps1", "--create", "--db", db])

        # submitted and autograded exist, but not in the database
        self._empty_notebook(join(course_dir, "submitted", "foo", "ps1", "problem1.ipynb"))
        timestamp = datetime.now()
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "timestamp.txt"), contents=timestamp.isoformat())
        self._empty_notebook(join(course_dir, "autograded", "foo", "ps1", "problem1.ipynb"))
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "timestamp.txt"), contents=timestamp.isoformat())
        assert api.get_autograded_students("ps1") == set([])

        # run autograde so things are consistent
        run_nbgrader(["autograde", "ps1", "--create", "--no-execute", "--force", "--db", db])
        assert api.get_autograded_students("ps1") == {"foo"}

        # updated submission
        timestamp = datetime.now()
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "timestamp.txt"), contents=timestamp.isoformat())
        assert api.get_autograded_students("ps1") == set([])

    def test_get_autograded_students_no_timestamps(self, api, course_dir, db):
        self._empty_notebook(join(course_dir, "source", "ps1", "problem1.ipynb"))
        run_nbgrader(["assign", "ps1", "--create", "--db", db])

        # submitted and autograded exist, but not in the database
        self._empty_notebook(join(course_dir, "submitted", "foo", "ps1", "problem1.ipynb"))
        self._empty_notebook(join(course_dir, "autograded", "foo", "ps1", "problem1.ipynb"))
        assert api.get_autograded_students("ps1") == set([])

        # run autograde so things are consistent
        run_nbgrader(["autograde", "ps1", "--create", "--no-execute", "--force", "--db", db])
        assert api.get_autograded_students("ps1") == {"foo"}

        # updated submission
        timestamp = datetime.now()
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "timestamp.txt"), contents=timestamp.isoformat())
        assert api.get_autograded_students("ps1") == set([])


    def test_get_assignment(self, api, course_dir, db, exchange):
        keys = set([
            'average_code_score', 'average_score', 'average_written_score',
            'duedate', 'name', 'num_submissions', 'release_path', 'releaseable',
            'source_path', 'status', 'id', 'max_code_score', 'max_score',
            'max_written_score', 'display_duedate', 'duedate_timezone',
            'duedate_notimezone'])

        default = {
            "average_code_score": 0,
            "average_score": 0,
            "average_written_score": 0,
            "duedate": None,
            "display_duedate": None,
            "duedate_timezone": "UTC",
            "duedate_notimezone": None,
            "name": "ps1",
            "num_submissions": 0,
            "release_path": None,
            "releaseable": True if sys.platform != 'win32' else False,
            "source_path": join("source", "ps1"),
            "status": "draft",
            "id": None,
            "max_code_score": 0,
            "max_score": 0,
            "max_written_score": 0
        }

        # check that return value is None when there is no assignment
        a = api.get_assignment("ps1")
        assert a is None

        # check the values when the source assignment exists, but hasn't been
        # released yet
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        a = api.get_assignment("ps1")
        assert set(a.keys()) == keys
        target = default.copy()
        assert a == target

        # check that it is not releasable if the course id isn't set
        api.course_id = None
        a = api.get_assignment("ps1")
        assert set(a.keys()) == keys
        target = default.copy()
        target["releaseable"] = False
        assert a == target

        # check the values once the student version of the assignment has been created
        api.course_id = "abc101"
        run_nbgrader(["assign", "ps1", "--create", "--db", db])
        a = api.get_assignment("ps1")
        assert set(a.keys()) == keys
        target = default.copy()
        target["release_path"] = join("release", "ps1")
        target["id"] = a["id"]
        target["max_code_score"] = 5
        target["max_score"] = 6
        target["max_written_score"] = 1
        assert a == target

        # check that timestamps are handled correctly
        with api.gradebook as gb:
            assignment = gb.find_assignment("ps1")
            assignment.duedate = parse_utc("2017-07-05 12:22:08 UTC")
            gb.db.commit()

        a = api.get_assignment("ps1")
        default["duedate"] = "2017-07-05T12:22:08"
        default["display_duedate"] = "2017-07-05 12:22:08 {}".format(self.tz)
        default["duedate_notimezone"] = "2017-07-05T12:22:08"
        assert a["duedate"] == default["duedate"]
        assert a["display_duedate"] == default["display_duedate"]
        assert a["duedate_notimezone"] == default["duedate_notimezone"]
        assert a["duedate_timezone"] == default["duedate_timezone"]

        # check the values once the assignment has been released and unreleased
        if sys.platform != "win32":
            run_nbgrader(["release", "ps1", "--course", "abc101", "--Exchange.root={}".format(exchange)])
            a = api.get_assignment("ps1")
            assert set(a.keys()) == keys
            target = default.copy()
            target["release_path"] = join("release", "ps1")
            target["id"] = a["id"]
            target["max_code_score"] = 5
            target["max_score"] = 6
            target["max_written_score"] = 1
            target["releaseable"] = True
            target["status"] = "released"
            assert a == target

            run_nbgrader(["list", "ps1", "--course", "abc101", "--Exchange.root={}".format(exchange), "--remove"])
            a = api.get_assignment("ps1")
            assert set(a.keys()) == keys
            target = default.copy()
            target["release_path"] = join("release", "ps1")
            target["id"] = a["id"]
            target["max_code_score"] = 5
            target["max_score"] = 6
            target["max_written_score"] = 1
            assert a == target

        # check the values once there are submissions as well
        self._empty_notebook(join(course_dir, "submitted", "foo", "ps1", "problem1.ipynb"))
        self._empty_notebook(join(course_dir, "submitted", "bar", "ps1", "problem1.ipynb"))
        a = api.get_assignment("ps1")
        assert set(a.keys()) == keys
        target = default.copy()
        target["release_path"] = join("release", "ps1")
        target["id"] = a["id"]
        target["max_code_score"] = 5
        target["max_score"] = 6
        target["max_written_score"] = 1
        target["num_submissions"] = 2
        assert a == target

    def test_get_assignments(self, api, course_dir):
        assert api.get_assignments() == []

        self._empty_notebook(join(course_dir, "source", "ps1", "problem1.ipynb"))
        self._empty_notebook(join(course_dir, "source", "ps2", "problem1.ipynb"))
        a = api.get_assignments()
        assert len(a) == 2
        assert a[0] == api.get_assignment("ps1")
        assert a[1] == api.get_assignment("ps2")

    def test_get_notebooks(self, api, course_dir, db):
        keys = set([
            'average_code_score', 'average_score', 'average_written_score',
            'name', 'id', 'max_code_score', 'max_score', 'max_written_score',
            'needs_manual_grade', 'num_submissions'])

        default = {
            "name": "p1",
            "id": None,
            "average_code_score": 0,
            "max_code_score": 0,
            "average_score": 0,
            "max_score": 0,
            "average_written_score": 0,
            "max_written_score": 0,
            "needs_manual_grade": False,
            "num_submissions": 0
        }

        # check that return value is None when there is no assignment
        n = api.get_notebooks("ps1")
        assert n == []

        # check values before nbgrader assign is run
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        n1, = api.get_notebooks("ps1")
        assert set(n1.keys()) == keys
        assert n1 == default.copy()

        # add it to the database (but don't assign yet)
        with api.gradebook as gb:
            gb.update_or_create_assignment("ps1")
        n1, = api.get_notebooks("ps1")
        assert set(n1.keys()) == keys
        assert n1 == default.copy()

        # check values after nbgrader assign is run
        run_nbgrader(["assign", "ps1", "--create", "--db", db, "--force"])
        n1, = api.get_notebooks("ps1")
        assert set(n1.keys()) == keys
        target = default.copy()
        target["id"] = n1["id"]
        target["max_code_score"] = 5
        target["max_score"] = 6
        target["max_written_score"] = 1
        assert n1 == target

    def test_get_submission(self, api, course_dir, db):
        keys = set([
            "id", "name", "student", "last_name", "first_name", "score",
            "max_score", "code_score", "max_code_score", "written_score",
            "max_written_score", "needs_manual_grade", "autograded",
            "timestamp", "submitted", "display_timestamp"])

        default = {
            "id": None,
            "name": "ps1",
            "student": "foo",
            "last_name": None,
            "first_name": None,
            "score": 0,
            "max_score": 0,
            "code_score": 0,
            "max_code_score": 0,
            "written_score": 0,
            "max_written_score": 0,
            "needs_manual_grade": False,
            "autograded": False,
            "timestamp": None,
            "display_timestamp": None,
            "submitted": False
        }

        s = api.get_submission("ps1", "foo")
        assert s == default.copy()

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        run_nbgrader(["assign", "ps1", "--create", "--db", db])

        self._copy_file(join("files", "submitted-changed.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "timestamp.txt"), contents="2017-07-05T12:32:56.123456")
        s = api.get_submission("ps1", "foo")
        assert set(s.keys()) == keys
        target = default.copy()
        target["submitted"] = True
        target["timestamp"] = "2017-07-05T12:32:56.123456"
        target["display_timestamp"] = "2017-07-05 12:32:56 {}".format(self.tz)
        assert s == target

        run_nbgrader(["autograde", "ps1", "--create", "--no-execute", "--force", "--db", db])
        s = api.get_submission("ps1", "foo")
        target = default.copy()
        target["id"] = s["id"]
        target["autograded"] = True
        target["submitted"] = True
        target["timestamp"] = "2017-07-05T12:32:56.123456"
        target["display_timestamp"] = "2017-07-05 12:32:56 {}".format(self.tz)
        target["code_score"] = 2
        target["max_code_score"] = 5
        target["score"] = 2
        target["max_score"] = 7
        target["written_score"] = 0
        target["max_written_score"] = 2
        target["needs_manual_grade"] = True
        assert s == target

    def test_get_submission_no_timestamp(self, api, course_dir, db):
        keys = set([
            "id", "name", "student", "last_name", "first_name", "score",
            "max_score", "code_score", "max_code_score", "written_score",
            "max_written_score", "needs_manual_grade", "autograded",
            "timestamp", "submitted", "display_timestamp"])

        default = {
            "id": None,
            "name": "ps1",
            "student": "foo",
            "last_name": None,
            "first_name": None,
            "score": 0,
            "max_score": 0,
            "code_score": 0,
            "max_code_score": 0,
            "written_score": 0,
            "max_written_score": 0,
            "needs_manual_grade": False,
            "autograded": False,
            "timestamp": None,
            "display_timestamp": None,
            "submitted": False
        }

        s = api.get_submission("ps1", "foo")
        assert s == default.copy()

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        run_nbgrader(["assign", "ps1", "--create", "--db", db])

        self._copy_file(join("files", "submitted-changed.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        s = api.get_submission("ps1", "foo")
        assert set(s.keys()) == keys
        target = default.copy()
        target["submitted"] = True
        assert s == target

        run_nbgrader(["autograde", "ps1", "--create", "--no-execute", "--force", "--db", db])
        s = api.get_submission("ps1", "foo")
        target = default.copy()
        target["id"] = s["id"]
        target["autograded"] = True
        target["submitted"] = True
        target["code_score"] = 2
        target["max_code_score"] = 5
        target["score"] = 2
        target["max_score"] = 7
        target["written_score"] = 0
        target["max_written_score"] = 2
        target["needs_manual_grade"] = True
        assert s == target

    def test_get_submissions(self, api, course_dir, db):
        assert api.get_submissions("ps1") == []

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        run_nbgrader(["assign", "ps1", "--create", "--db", db])

        self._copy_file(join("files", "submitted-changed.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        timestamp = datetime.now()
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "timestamp.txt"), contents=timestamp.isoformat())
        s1, = api.get_submissions("ps1")
        assert s1 == api.get_submission("ps1", "foo")

        run_nbgrader(["autograde", "ps1", "--create", "--no-execute", "--force", "--db", db])
        s1, = api.get_submissions("ps1")
        assert s1 == api.get_submission("ps1", "foo")

    def test_filter_existing_notebooks(self, api, course_dir, db):
        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p2.ipynb"))
        run_nbgrader(["assign", "ps1", "--create", "--db", db])

        self._copy_file(join("files", "submitted-changed.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        run_nbgrader(["autograde", "ps1", "--create", "--no-execute", "--force", "--db", db])

        with api.gradebook as gb:
            notebooks = gb.notebook_submissions("p1", "ps1")
            s = api._filter_existing_notebooks("ps1", notebooks)
            assert s == notebooks

            notebooks = gb.notebook_submissions("p2", "ps1")
            s = api._filter_existing_notebooks("ps1", notebooks)
            assert s == []

    def test_get_notebook_submission_indices(self, api, course_dir, db):
        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        run_nbgrader(["assign", "ps1", "--create", "--db", db])

        self._copy_file(join("files", "submitted-changed.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        self._copy_file(join("files", "submitted-changed.ipynb"), join(course_dir, "submitted", "bar", "ps1", "p1.ipynb"))
        run_nbgrader(["autograde", "ps1", "--create", "--no-execute", "--force", "--db", db])

        with api.gradebook as gb:
            notebooks = gb.notebook_submissions("p1", "ps1")
            notebooks.sort(key=lambda x: x.id)
            idx = api.get_notebook_submission_indices("ps1", "p1")
            assert idx[notebooks[0].id] == 0
            assert idx[notebooks[1].id] == 1

    def test_get_notebook_submissions(self, api, course_dir, db):
        assert api.get_notebook_submissions("ps1", "p1") == []

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        run_nbgrader(["assign", "ps1", "--create", "--db", db])

        self._copy_file(join("files", "submitted-changed.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        self._copy_file(join("files", "submitted-changed.ipynb"), join(course_dir, "submitted", "bar", "ps1", "p1.ipynb"))
        run_nbgrader(["autograde", "ps1", "--create", "--no-execute", "--force", "--db", db])
        self._copy_file(join("files", "submitted-changed.ipynb"), join(course_dir, "submitted", "baz", "ps1", "p1.ipynb"))

        s = api.get_notebook_submissions("ps1", "p1")
        assert len(s) == 2
        with api.gradebook as gb:
            notebooks = gb.notebook_submissions("p1", "ps1")
            notebooks.sort(key=lambda x: x.id)
            notebooks = [x.to_dict() for x in notebooks]
            for i in range(2):
                notebooks[i]["index"] = i
                assert s[i] == notebooks[i]

    def test_get_student(self, api, course_dir, db):
        assert api.get_student("foo") is None

        self._copy_file(join("files", "submitted-changed.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        assert api.get_student("foo") == {
            "id": "foo",
            "last_name": None,
            "first_name": None,
            "email": None,
            "max_score": 0,
            "score": 0
        }
        rmtree(join(course_dir, "submitted", "foo"))

        with api.gradebook as gb:
            gb.add_student("foo")
            assert api.get_student("foo") == {
                "id": "foo",
                "last_name": None,
                "first_name": None,
                "email": None,
                "max_score": 0,
                "score": 0
            }

            gb.update_or_create_student("foo", last_name="Foo", first_name="A", email="a.foo@email.com")
            assert api.get_student("foo") == {
                "id": "foo",
                "last_name": "Foo",
                "first_name": "A",
                "email": "a.foo@email.com",
                "max_score": 0,
                "score": 0
            }

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        run_nbgrader(["assign", "ps1", "--create", "--db", db])
        self._copy_file(join("files", "submitted-changed.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        run_nbgrader(["autograde", "ps1", "--create", "--no-execute", "--force", "--db", db])
        assert api.get_student("foo") == {
            "id": "foo",
            "last_name": "Foo",
            "first_name": "A",
            "email": "a.foo@email.com",
            "max_score": 7,
            "score": 2
        }

    def test_get_students(self, api, course_dir):
        assert api.get_students() == []

        with api.gradebook as gb:
            gb.update_or_create_student("foo", last_name="Foo", first_name="A", email="a.foo@email.com")
            s1 = {
                "id": "foo",
                "last_name": "Foo",
                "first_name": "A",
                "email": "a.foo@email.com",
                "max_score": 0,
                "score": 0
            }
            assert api.get_students() == [s1]

        self._copy_file(join("files", "submitted-changed.ipynb"), join(course_dir, "submitted", "bar", "ps1", "p1.ipynb"))
        s2 = {
            "id": "bar",
            "last_name": None,
            "first_name": None,
            "email": None,
            "max_score": 0,
            "score": 0
        }
        assert api.get_students() == [s1, s2]

    def test_get_student_submissions(self, api, course_dir, db):
        assert api.get_student_submissions("foo") == []

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        run_nbgrader(["assign", "ps1", "--create", "--db", db])
        self._copy_file(join("files", "submitted-changed.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        timestamp = datetime.now()
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "timestamp.txt"), contents=timestamp.isoformat())
        run_nbgrader(["autograde", "ps1", "--create", "--no-execute", "--force", "--db", db])

        assert api.get_student_submissions("foo") == [api.get_submission("ps1", "foo")]

    def test_get_student_notebook_submissions(self, api, course_dir, db):
        assert api.get_student_notebook_submissions("foo", "ps1") == []

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p2.ipynb"))
        run_nbgrader(["assign", "ps1", "--create", "--db", db])

        self._copy_file(join("files", "submitted-changed.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        run_nbgrader(["autograde", "ps1", "--create", "--no-execute", "--force", "--db", db])

        s_p1, s_p2 = api.get_student_notebook_submissions("foo", "ps1")
        p1, = api.get_notebook_submissions("ps1", "p1")
        del p1["index"]
        assert s_p1 == p1
        assert s_p2 == {
            "id": None,
            "name": "p2",
            "student": "foo",
            "last_name": None,
            "first_name": None,
            "score": 0,
            "max_score": 7,
            "code_score": 0,
            "max_code_score": 5,
            "written_score": 0,
            "max_written_score": 2,
            "needs_manual_grade": False,
            "failed_tests": False,
            "flagged": False
        }

    def test_assign(self, api, course_dir, db):
        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        result = api.assign("ps1")
        assert result["success"]
        assert os.path.exists(join(course_dir, "release", "ps1", "p1.ipynb"))

        os.makedirs(join(course_dir, "source", "ps2"))
        result = api.assign("ps2")
        assert not result["success"]

    @notwindows
    def test_release_and_unrelease(self, api, course_dir, db, exchange):
        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        result = api.assign("ps1")
        result = api.release("ps1")
        assert result["success"]
        assert os.path.exists(join(exchange, "abc101", "outbound", "ps1", "p1.ipynb"))

        result = api.release("ps1")
        assert not result["success"]

        result = api.unrelease("ps1")
        assert result["success"]
        assert not os.path.exists(join(exchange, "abc101", "outbound", "ps1", "p1.ipynb"))

    @notwindows
    def test_collect(self, api, course_dir, db, exchange):
        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        result = api.assign("ps1")
        result = api.release("ps1")
        result = api.collect("ps1")
        assert result["success"]
        assert "No submissions" in result["log"]

        run_nbgrader(["fetch", "ps1", "--course", "abc101", "--Exchange.root={}".format(exchange)])
        run_nbgrader(["submit", "ps1", "--course", "abc101", "--Exchange.root={}".format(exchange)])
        username = get_username()
        result = api.collect("ps1")
        assert result["success"]
        assert "Collecting submission" in result["log"]
        assert os.path.exists(join(course_dir, "submitted", username, "ps1", "p1.ipynb"))

        run_nbgrader(["submit", "ps1", "--course", "abc101", "--Exchange.root={}".format(exchange)])
        result = api.collect("ps1")
        assert result["success"]
        assert "Updating submission" in result["log"]
        assert os.path.exists(join(course_dir, "submitted", username, "ps1", "p1.ipynb"))

    def test_autograde(self, api, course_dir, db):
        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        api.assign("ps1")

        result = api.autograde("ps1", "foo")
        assert not result["success"]
        assert "No notebooks were matched" in result["log"]

        self._copy_file(join("files", "submitted-changed.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        result = api.autograde("ps1", "foo")
        assert result["success"]
        assert os.path.exists(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))

        result = api.autograde("ps1", "foo")
        assert result["success"]

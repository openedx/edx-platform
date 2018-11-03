import pytest

from datetime import datetime
from ... import api
from ... import utils
from ...api import InvalidEntry, MissingEntry

@pytest.fixture
def gradebook(request):
    gb = api.Gradebook("sqlite:///:memory:")
    def fin():
        gb.close()
    request.addfinalizer(fin)
    return gb


@pytest.fixture
def assignment(gradebook):
    gradebook.add_assignment('foo')
    gradebook.add_notebook('p1', 'foo')
    gradebook.add_grade_cell('test1', 'p1', 'foo', max_score=1, cell_type='code')
    gradebook.add_grade_cell('test2', 'p1', 'foo', max_score=2, cell_type='markdown')
    gradebook.add_solution_cell('solution1', 'p1', 'foo')
    gradebook.add_solution_cell('test2', 'p1', 'foo')
    gradebook.add_source_cell('test1', 'p1', 'foo', cell_type='code')
    gradebook.add_source_cell('test2', 'p1', 'foo', cell_type='markdown')
    gradebook.add_source_cell('solution1', 'p1', 'foo', cell_type='code')
    return gradebook


def test_init(gradebook):
    assert gradebook.students == []
    assert gradebook.assignments == []


#### Test students

def test_add_student(gradebook):
    s = gradebook.add_student('12345')
    assert s.id == '12345'
    assert gradebook.students == [s]

    # try adding a duplicate student
    with pytest.raises(InvalidEntry):
        gradebook.add_student('12345')

    # try adding a student with arguments
    s = gradebook.add_student('6789', last_name="Bar", first_name="Foo", email="foo@bar.com")
    assert s.id == '6789'
    assert s.last_name == "Bar"
    assert s.first_name == "Foo"
    assert s.email == "foo@bar.com"


def test_add_duplicate_student(gradebook):
    # we also need this test because this will cause an IntegrityError
    # under the hood rather than a FlushError
    gradebook.add_student('12345')
    with pytest.raises(InvalidEntry):
        gradebook.add_student('12345')


def test_find_student(gradebook):
    s1 = gradebook.add_student('12345')
    assert gradebook.find_student('12345') == s1

    s2 = gradebook.add_student('abcd')
    assert gradebook.find_student('12345') == s1
    assert gradebook.find_student('abcd') == s2


def test_find_nonexistant_student(gradebook):
    with pytest.raises(MissingEntry):
        gradebook.find_student('12345')


def test_remove_student(assignment):
    assignment.add_student('hacker123')
    assignment.add_submission('foo', 'hacker123')

    assignment.remove_student('hacker123')

    with pytest.raises(MissingEntry):
        assignment.find_submission('foo', 'hacker123')
    with pytest.raises(MissingEntry):
        assignment.find_student('hacker123')


def test_update_or_create_student(gradebook):
    # first test creating it
    s1 = gradebook.update_or_create_student('hacker123')
    assert gradebook.find_student('hacker123') == s1
    assert s1.first_name is None

    # now test finding/updating it
    s2 = gradebook.update_or_create_student('hacker123', first_name='Alyssa')
    assert s1 == s2
    assert s2.first_name == 'Alyssa'


#### Test assignments

def test_add_assignment(gradebook):
    a = gradebook.add_assignment('foo')
    assert a.name == 'foo'
    assert gradebook.assignments == [a]

    # try adding a duplicate assignment
    with pytest.raises(InvalidEntry):
        gradebook.add_assignment('foo')

    # try adding an assignment with arguments
    now = datetime.utcnow()
    a = gradebook.add_assignment('bar', duedate=now)
    assert a.name == 'bar'
    assert a.duedate == now

    # try adding with a string timestamp
    a = gradebook.add_assignment('baz', duedate=now.isoformat())
    assert a.name == 'baz'
    assert a.duedate == now


def test_add_duplicate_assignment(gradebook):
    gradebook.add_assignment('foo')
    with pytest.raises(InvalidEntry):
        gradebook.add_assignment('foo')


def test_find_assignment(gradebook):
    a1 = gradebook.add_assignment('foo')
    assert gradebook.find_assignment('foo') == a1

    a2 = gradebook.add_assignment('bar')
    assert gradebook.find_assignment('foo') == a1
    assert gradebook.find_assignment('bar') == a2


def test_find_nonexistant_assignment(gradebook):
    with pytest.raises(MissingEntry):
        gradebook.find_assignment('foo')


def test_remove_assignment(assignment):
    assignment.add_student('hacker123')
    assignment.add_submission('foo', 'hacker123')

    notebooks = assignment.find_assignment('foo').notebooks
    grade_cells = [x for nb in notebooks for x in nb.grade_cells]
    solution_cells = [x for nb in notebooks for x in nb.solution_cells]
    source_cells = [x for nb in notebooks for x in nb.source_cells]

    assignment.remove_assignment('foo')

    for nb in notebooks:
        assert assignment.db.query(api.SubmittedNotebook).filter(api.SubmittedNotebook.id == nb.id).all() == []
    for grade_cell in grade_cells:
        assert assignment.db.query(api.GradeCell).filter(api.GradeCell.id == grade_cell.id).all() == []
    for solution_cell in solution_cells:
        assert assignment.db.query(api.SolutionCell).filter(api.SolutionCell.id == solution_cell.id).all() == []
    for source_cell in source_cells:
        assert assignment.db.query(api.SourceCell).filter(api.SourceCell.id == source_cell.id).all() == []

    with pytest.raises(MissingEntry):
        assignment.find_assignment('foo')

    assert assignment.find_student('hacker123').submissions == []


def test_update_or_create_assignment(gradebook):
    # first test creating it
    a1 = gradebook.update_or_create_assignment('foo')
    assert gradebook.find_assignment('foo') == a1
    assert a1.duedate is None

    # now test finding/updating it
    a2 = gradebook.update_or_create_assignment('foo', duedate="2015-02-02 14:58:23.948203 PST")
    assert a1 == a2
    assert a2.duedate == utils.parse_utc("2015-02-02 14:58:23.948203 PST")


#### Test notebooks

def test_add_notebook(gradebook):
    a = gradebook.add_assignment('foo')
    n = gradebook.add_notebook('p1', 'foo')
    assert n.name == 'p1'
    assert n.assignment == a
    assert a.notebooks == [n]

    # try adding a duplicate assignment
    with pytest.raises(InvalidEntry):
        gradebook.add_notebook('p1', 'foo')


def test_add_duplicate_notebook(gradebook):
    # it should be ok to add a notebook with the same name, as long as
    # it's for different assignments
    gradebook.add_assignment('foo')
    gradebook.add_assignment('bar')
    n1 = gradebook.add_notebook('p1', 'foo')
    n2 = gradebook.add_notebook('p1', 'bar')
    assert n1.id != n2.id

    # but not ok to add a notebook with the same name for the same assignment
    with pytest.raises(InvalidEntry):
        gradebook.add_notebook('p1', 'foo')


def test_find_notebook(gradebook):
    gradebook.add_assignment('foo')
    n1 = gradebook.add_notebook('p1', 'foo')
    assert gradebook.find_notebook('p1', 'foo') == n1

    n2 = gradebook.add_notebook('p2', 'foo')
    assert gradebook.find_notebook('p1', 'foo') == n1
    assert gradebook.find_notebook('p2', 'foo') == n2


def test_find_nonexistant_notebook(gradebook):
    # check that it doesn't find it when there is nothing in the db
    with pytest.raises(MissingEntry):
        gradebook.find_notebook('p1', 'foo')

    # check that it doesn't find it even if the assignment exists
    gradebook.add_assignment('foo')
    with pytest.raises(MissingEntry):
        gradebook.find_notebook('p1', 'foo')


def test_update_or_create_notebook(gradebook):
    # first test creating it
    gradebook.add_assignment('foo')
    n1 = gradebook.update_or_create_notebook('p1', 'foo')
    assert gradebook.find_notebook('p1', 'foo') == n1

    # now test finding/updating it
    n2 = gradebook.update_or_create_notebook('p1', 'foo')
    assert n1 == n2


def test_remove_notebook(assignment):
    assignment.add_student('hacker123')
    assignment.add_submission('foo', 'hacker123')

    notebooks = assignment.find_assignment('foo').notebooks

    for nb in notebooks:
        grade_cells = [x for x in nb.grade_cells]
        solution_cells = [x for x in nb.solution_cells]
        source_cells = [x for x in nb.source_cells]

        assignment.remove_notebook(nb.name, 'foo')
        assert assignment.db.query(api.SubmittedNotebook).filter(api.SubmittedNotebook.id == nb.id).all() == []

        for grade_cell in grade_cells:
            assert assignment.db.query(api.GradeCell).filter(api.GradeCell.id == grade_cell.id).all() == []
        for solution_cell in solution_cells:
            assert assignment.db.query(api.SolutionCell).filter(api.SolutionCell.id == solution_cell.id).all() == []
        for source_cell in source_cells:
            assert assignment.db.query(api.SourceCell).filter(api.SourceCell.id == source_cell.id).all() == []

        with pytest.raises(MissingEntry):
            assignment.find_notebook(nb.name, 'foo')


#### Test grade cells

def test_add_grade_cell(gradebook):
    gradebook.add_assignment('foo')
    n = gradebook.add_notebook('p1', 'foo')
    gc = gradebook.add_grade_cell('test1', 'p1', 'foo', max_score=2, cell_type='markdown')
    assert gc.name == 'test1'
    assert gc.max_score == 2
    assert gc.cell_type == 'markdown'
    assert n.grade_cells == [gc]
    assert gc.notebook == n


def test_add_grade_cell_with_args(gradebook):
    gradebook.add_assignment('foo')
    gradebook.add_notebook('p1', 'foo')
    gc = gradebook.add_grade_cell(
        'test1', 'p1', 'foo',
        max_score=3, cell_type="code")
    assert gc.name == 'test1'
    assert gc.max_score == 3
    assert gc.cell_type == "code"


def test_create_invalid_grade_cell(gradebook):
    gradebook.add_assignment('foo')
    gradebook.add_notebook('p1', 'foo')
    with pytest.raises(InvalidEntry):
        gradebook.add_grade_cell(
            'test1', 'p1', 'foo',
            max_score=3, cell_type="something")


def test_add_duplicate_grade_cell(gradebook):
    gradebook.add_assignment('foo')
    gradebook.add_notebook('p1', 'foo')
    gradebook.add_grade_cell('test1', 'p1', 'foo', max_score=1, cell_type='code')
    with pytest.raises(InvalidEntry):
        gradebook.add_grade_cell('test1', 'p1', 'foo', max_score=2, cell_type='markdown')


def test_find_grade_cell(gradebook):
    gradebook.add_assignment('foo')
    gradebook.add_notebook('p1', 'foo')
    gc1 = gradebook.add_grade_cell('test1', 'p1', 'foo', max_score=1, cell_type='code')
    assert gradebook.find_grade_cell('test1', 'p1', 'foo') == gc1

    gc2 = gradebook.add_grade_cell('test2', 'p1', 'foo', max_score=2, cell_type='code')
    assert gradebook.find_grade_cell('test1', 'p1', 'foo') == gc1
    assert gradebook.find_grade_cell('test2', 'p1', 'foo') == gc2


def test_find_nonexistant_grade_cell(gradebook):
    with pytest.raises(MissingEntry):
        gradebook.find_grade_cell('test1', 'p1', 'foo')

    gradebook.add_assignment('foo')
    with pytest.raises(MissingEntry):
        gradebook.find_grade_cell('test1', 'p1', 'foo')

    gradebook.add_notebook('p1', 'foo')
    with pytest.raises(MissingEntry):
        gradebook.find_grade_cell('test1', 'p1', 'foo')


def test_update_or_create_grade_cell(gradebook):
    # first test creating it
    gradebook.add_assignment('foo')
    gradebook.add_notebook('p1', 'foo')
    gc1 = gradebook.update_or_create_grade_cell('test1', 'p1', 'foo', max_score=2, cell_type='code')
    assert gc1.max_score == 2
    assert gc1.cell_type == 'code'
    assert gradebook.find_grade_cell('test1', 'p1', 'foo') == gc1

    # now test finding/updating it
    gc2 = gradebook.update_or_create_grade_cell('test1', 'p1', 'foo', max_score=3)
    assert gc1 == gc2
    assert gc1.max_score == 3
    assert gc1.cell_type == 'code'


#### Test solution cells

def test_add_solution_cell(gradebook):
    gradebook.add_assignment('foo')
    n = gradebook.add_notebook('p1', 'foo')
    sc = gradebook.add_solution_cell('test1', 'p1', 'foo')
    assert sc.name == 'test1'
    assert n.solution_cells == [sc]
    assert sc.notebook == n


def test_add_duplicate_solution_cell(gradebook):
    gradebook.add_assignment('foo')
    gradebook.add_notebook('p1', 'foo')
    gradebook.add_solution_cell('test1', 'p1', 'foo')
    with pytest.raises(InvalidEntry):
        gradebook.add_solution_cell('test1', 'p1', 'foo')


def test_find_solution_cell(gradebook):
    gradebook.add_assignment('foo')
    gradebook.add_notebook('p1', 'foo')
    sc1 = gradebook.add_solution_cell('test1', 'p1', 'foo')
    assert gradebook.find_solution_cell('test1', 'p1', 'foo') == sc1

    sc2 = gradebook.add_solution_cell('test2', 'p1', 'foo')
    assert gradebook.find_solution_cell('test1', 'p1', 'foo') == sc1
    assert gradebook.find_solution_cell('test2', 'p1', 'foo') == sc2


def test_find_nonexistant_solution_cell(gradebook):
    with pytest.raises(MissingEntry):
        gradebook.find_solution_cell('test1', 'p1', 'foo')

    gradebook.add_assignment('foo')
    with pytest.raises(MissingEntry):
        gradebook.find_solution_cell('test1', 'p1', 'foo')

    gradebook.add_notebook('p1', 'foo')
    with pytest.raises(MissingEntry):
        gradebook.find_solution_cell('test1', 'p1', 'foo')


def test_update_or_create_solution_cell(gradebook):
    # first test creating it
    gradebook.add_assignment('foo')
    gradebook.add_notebook('p1', 'foo')
    sc1 = gradebook.update_or_create_solution_cell('test1', 'p1', 'foo')
    assert gradebook.find_solution_cell('test1', 'p1', 'foo') == sc1

    # now test finding/updating it
    sc2 = gradebook.update_or_create_solution_cell('test1', 'p1', 'foo')
    assert sc1 == sc2


#### Test source cells

def test_add_source_cell(gradebook):
    gradebook.add_assignment('foo')
    n = gradebook.add_notebook('p1', 'foo')
    sc = gradebook.add_source_cell('test1', 'p1', 'foo', cell_type="code")
    assert sc.name == 'test1'
    assert sc.cell_type == 'code'
    assert n.source_cells == [sc]
    assert sc.notebook == n


def test_add_source_cell_with_args(gradebook):
    gradebook.add_assignment('foo')
    gradebook.add_notebook('p1', 'foo')
    sc = gradebook.add_source_cell(
        'test1', 'p1', 'foo',
        source="blah blah blah",
        cell_type="code", checksum="abcde")
    assert sc.name == 'test1'
    assert sc.source == "blah blah blah"
    assert sc.cell_type == "code"
    assert sc.checksum == "abcde"


def test_create_invalid_source_cell(gradebook):
    gradebook.add_assignment('foo')
    gradebook.add_notebook('p1', 'foo')
    with pytest.raises(InvalidEntry):
        gradebook.add_source_cell(
            'test1', 'p1', 'foo',
            source="blah blah blah",
            cell_type="something", checksum="abcde")


def test_add_duplicate_source_cell(gradebook):
    gradebook.add_assignment('foo')
    gradebook.add_notebook('p1', 'foo')
    gradebook.add_source_cell('test1', 'p1', 'foo', cell_type="code")
    with pytest.raises(InvalidEntry):
        gradebook.add_source_cell('test1', 'p1', 'foo', cell_type="code")


def test_find_source_cell(gradebook):
    gradebook.add_assignment('foo')
    gradebook.add_notebook('p1', 'foo')
    sc1 = gradebook.add_source_cell('test1', 'p1', 'foo', cell_type="code")
    assert gradebook.find_source_cell('test1', 'p1', 'foo') == sc1

    sc2 = gradebook.add_source_cell('test2', 'p1', 'foo', cell_type="code")
    assert gradebook.find_source_cell('test1', 'p1', 'foo') == sc1
    assert gradebook.find_source_cell('test2', 'p1', 'foo') == sc2


def test_find_nonexistant_source_cell(gradebook):
    with pytest.raises(MissingEntry):
        gradebook.find_source_cell('test1', 'p1', 'foo')

    gradebook.add_assignment('foo')
    with pytest.raises(MissingEntry):
        gradebook.find_source_cell('test1', 'p1', 'foo')

    gradebook.add_notebook('p1', 'foo')
    with pytest.raises(MissingEntry):
        gradebook.find_source_cell('test1', 'p1', 'foo')


def test_update_or_create_source_cell(gradebook):
    # first test creating it
    gradebook.add_assignment('foo')
    gradebook.add_notebook('p1', 'foo')
    sc1 = gradebook.update_or_create_source_cell('test1', 'p1', 'foo', cell_type='code')
    assert sc1.cell_type == 'code'
    assert gradebook.find_source_cell('test1', 'p1', 'foo') == sc1

    # now test finding/updating it
    assert sc1.checksum == None
    sc2 = gradebook.update_or_create_source_cell('test1', 'p1', 'foo', checksum="123456")
    assert sc1 == sc2
    assert sc1.cell_type == 'code'
    assert sc1.checksum == "123456"


#### Test submissions

def test_add_submission(assignment):
    assignment.add_student('hacker123')
    assignment.add_student('bitdiddle')
    s1 = assignment.add_submission('foo', 'hacker123')
    s2 = assignment.add_submission('foo', 'bitdiddle')

    assert assignment.assignment_submissions('foo') == [s2, s1]
    assert assignment.student_submissions('hacker123') == [s1]
    assert assignment.student_submissions('bitdiddle') == [s2]
    assert assignment.find_submission('foo', 'hacker123') == s1
    assert assignment.find_submission('foo', 'bitdiddle') == s2


def test_add_duplicate_submission(assignment):
    assignment.add_student('hacker123')
    assignment.add_submission('foo', 'hacker123')
    with pytest.raises(InvalidEntry):
        assignment.add_submission('foo', 'hacker123')


def test_remove_submission(assignment):
    assignment.add_student('hacker123')
    assignment.add_submission('foo', 'hacker123')

    submission = assignment.find_submission('foo', 'hacker123')
    notebooks = submission.notebooks
    grades = [x for nb in notebooks for x in nb.grades]
    comments = [x for nb in notebooks for x in nb.comments]

    assignment.remove_submission('foo', 'hacker123')

    for nb in notebooks:
        assert assignment.db.query(api.SubmittedNotebook).filter(api.SubmittedNotebook.id == nb.id).all() == []
    for grade in grades:
        assert assignment.db.query(api.Grade).filter(api.Grade.id == grade.id).all() == []
    for comment in comments:
        assert assignment.db.query(api.Comment).filter(api.Comment.id == comment.id).all() == []

    with pytest.raises(MissingEntry):
        assignment.find_submission('foo', 'hacker123')


def test_update_or_create_submission(assignment):
    assignment.add_student('hacker123')
    s1 = assignment.update_or_create_submission('foo', 'hacker123')
    assert s1.timestamp is None

    s2 = assignment.update_or_create_submission('foo', 'hacker123', timestamp="2015-02-02 14:58:23.948203 PST")
    assert s1 == s2
    assert s2.timestamp == utils.parse_utc("2015-02-02 14:58:23.948203 PST")


def test_find_submission_notebook(assignment):
    assignment.add_student('hacker123')
    s = assignment.add_submission('foo', 'hacker123')
    n1, = s.notebooks

    with pytest.raises(MissingEntry):
        assignment.find_submission_notebook('p2', 'foo', 'hacker123')

    n2 = assignment.find_submission_notebook('p1', 'foo', 'hacker123')
    assert n1 == n2


def test_find_submission_notebook_by_id(assignment):
    assignment.add_student('hacker123')
    s = assignment.add_submission('foo', 'hacker123')
    n1, = s.notebooks

    with pytest.raises(MissingEntry):
        assignment.find_submission_notebook_by_id('12345')

    n2 = assignment.find_submission_notebook_by_id(n1.id)
    assert n1 == n2


def test_remove_submission_notebook(assignment):
    assignment.add_student('hacker123')
    assignment.add_submission('foo', 'hacker123')

    submission = assignment.find_submission('foo', 'hacker123')
    notebooks = submission.notebooks

    for nb in notebooks:
        grades = [x for x in nb.grades]
        comments = [x for x in nb.comments]

        assignment.remove_submission_notebook(nb.name, 'foo', 'hacker123')
        assert assignment.db.query(api.SubmittedNotebook).filter(api.SubmittedNotebook.id == nb.id).all() == []

        for grade in grades:
            assert assignment.db.query(api.Grade).filter(api.Grade.id == grade.id).all() == []
        for comment in comments:
            assert assignment.db.query(api.Comment).filter(api.Comment.id == comment.id).all() == []

        with pytest.raises(MissingEntry):
            assignment.find_submission_notebook(nb.name, 'foo', 'hacker123')


def test_find_grade(assignment):
    assignment.add_student('hacker123')
    s = assignment.add_submission('foo', 'hacker123')
    n1, = s.notebooks
    grades = n1.grades

    for g1 in grades:
        g2 = assignment.find_grade(g1.name, 'p1', 'foo', 'hacker123')
        assert g1 == g2

    with pytest.raises(MissingEntry):
        assignment.find_grade('asdf', 'p1', 'foo', 'hacker123')


def test_find_grade_by_id(assignment):
    assignment.add_student('hacker123')
    s = assignment.add_submission('foo', 'hacker123')
    n1, = s.notebooks
    grades = n1.grades

    for g1 in grades:
        g2 = assignment.find_grade_by_id(g1.id)
        assert g1 == g2

    with pytest.raises(MissingEntry):
        assignment.find_grade_by_id('12345')


def test_find_comment(assignment):
    assignment.add_student('hacker123')
    s = assignment.add_submission('foo', 'hacker123')
    n1, = s.notebooks
    comments = n1.comments

    for c1 in comments:
        c2 = assignment.find_comment(c1.name, 'p1', 'foo', 'hacker123')
        assert c1 == c2

    with pytest.raises(MissingEntry):
        assignment.find_comment('asdf', 'p1', 'foo', 'hacker123')


def test_find_comment_by_id(assignment):
    assignment.add_student('hacker123')
    s = assignment.add_submission('foo', 'hacker123')
    n1, = s.notebooks
    comments = n1.comments

    for c1 in comments:
        c2 = assignment.find_comment_by_id(c1.id)
        assert c1 == c2

    with pytest.raises(MissingEntry):
        assignment.find_comment_by_id('12345')


### Test average scores

def test_average_assignment_score(assignment):
    assert assignment.average_assignment_score('foo') == 0.0
    assert assignment.average_assignment_code_score('foo') == 0.0
    assert assignment.average_assignment_written_score('foo') == 0.0

    assignment.add_student('hacker123')
    assignment.add_student('bitdiddle')
    assignment.add_submission('foo', 'hacker123')
    assignment.add_submission('foo', 'bitdiddle')

    assert assignment.average_assignment_score('foo') == 0.0
    assert assignment.average_assignment_code_score('foo') == 0.0
    assert assignment.average_assignment_written_score('foo') == 0.0

    g1 = assignment.find_grade("test1", "p1", "foo", "hacker123")
    g2 = assignment.find_grade("test2", "p1", "foo", "hacker123")
    g3 = assignment.find_grade("test1", "p1", "foo", "bitdiddle")
    g4 = assignment.find_grade("test2", "p1", "foo", "bitdiddle")

    g1.manual_score = 0.5
    g2.manual_score = 2
    g3.manual_score = 1
    g4.manual_score = 1
    assignment.db.commit()

    assert assignment.average_assignment_score('foo') == 2.25
    assert assignment.average_assignment_code_score('foo') == 0.75
    assert assignment.average_assignment_written_score('foo') == 1.5


def test_average_notebook_score(assignment):
    assert assignment.average_notebook_score('p1', 'foo') == 0
    assert assignment.average_notebook_code_score('p1', 'foo') == 0
    assert assignment.average_notebook_written_score('p1', 'foo') == 0

    assignment.add_student('hacker123')
    assignment.add_student('bitdiddle')
    assignment.add_submission('foo', 'hacker123')
    assignment.add_submission('foo', 'bitdiddle')

    assert assignment.average_notebook_score('p1', 'foo') == 0.0
    assert assignment.average_notebook_code_score('p1', 'foo') == 0.0
    assert assignment.average_notebook_written_score('p1', 'foo') == 0.0

    g1 = assignment.find_grade("test1", "p1", "foo", "hacker123")
    g2 = assignment.find_grade("test2", "p1", "foo", "hacker123")
    g3 = assignment.find_grade("test1", "p1", "foo", "bitdiddle")
    g4 = assignment.find_grade("test2", "p1", "foo", "bitdiddle")

    g1.manual_score = 0.5
    g2.manual_score = 2
    g3.manual_score = 1
    g4.manual_score = 1
    assignment.db.commit()

    assert assignment.average_notebook_score('p1', 'foo') == 2.25
    assert assignment.average_notebook_code_score('p1', 'foo') == 0.75
    assert assignment.average_notebook_written_score('p1', 'foo') == 1.5


## Test mass dictionary queries

def test_student_dicts(assignment):
    assignment.add_student('hacker123')
    assignment.add_student('bitdiddle')
    assignment.add_student('louisreasoner')
    assignment.add_submission('foo', 'hacker123')
    assignment.add_submission('foo', 'bitdiddle')

    g1 = assignment.find_grade("test1", "p1", "foo", "hacker123")
    g2 = assignment.find_grade("test2", "p1", "foo", "hacker123")
    g3 = assignment.find_grade("test1", "p1", "foo", "bitdiddle")
    g4 = assignment.find_grade("test2", "p1", "foo", "bitdiddle")

    g1.manual_score = 0.5
    g2.manual_score = 2
    g3.manual_score = 1
    g4.manual_score = 1
    assignment.db.commit()

    students = assignment.student_dicts()
    a = sorted(students, key=lambda x: x["id"])
    b = sorted([x.to_dict() for x in assignment.students], key=lambda x: x["id"])
    assert a == b


def test_student_dicts_zero_points(gradebook):
    gradebook.add_assignment("ps1")
    s = gradebook.add_student("1234")
    assert gradebook.student_dicts() == [s.to_dict()]


def test_notebook_submission_dicts(assignment):
    assignment.add_student('hacker123')
    assignment.add_student('bitdiddle')
    s1 = assignment.add_submission('foo', 'hacker123')
    s2 = assignment.add_submission('foo', 'bitdiddle')
    s1.flagged = True
    s2.flagged = False

    g1 = assignment.find_grade("test1", "p1", "foo", "hacker123")
    g2 = assignment.find_grade("test2", "p1", "foo", "hacker123")
    g3 = assignment.find_grade("test1", "p1", "foo", "bitdiddle")
    g4 = assignment.find_grade("test2", "p1", "foo", "bitdiddle")

    g1.manual_score = 0.5
    g2.manual_score = 2
    g3.manual_score = 1
    g4.manual_score = 1
    assignment.db.commit()

    notebook = assignment.find_notebook("p1", "foo")
    submissions = assignment.notebook_submission_dicts("p1", "foo")
    a = sorted(submissions, key=lambda x: x["id"])
    b = sorted([x.to_dict() for x in notebook.submissions], key=lambda x: x["id"])
    assert a == b


def test_submission_dicts(assignment):
    assignment.add_student('hacker123')
    assignment.add_student('bitdiddle')
    s1 = assignment.add_submission('foo', 'hacker123')
    s2 = assignment.add_submission('foo', 'bitdiddle')
    s1.flagged = True
    s2.flagged = False

    g1 = assignment.find_grade("test1", "p1", "foo", "hacker123")
    g2 = assignment.find_grade("test2", "p1", "foo", "hacker123")
    g3 = assignment.find_grade("test1", "p1", "foo", "bitdiddle")
    g4 = assignment.find_grade("test2", "p1", "foo", "bitdiddle")

    g1.manual_score = 0.5
    g2.manual_score = 2
    g3.manual_score = 1
    g4.manual_score = 1
    assignment.db.commit()

    a = sorted(assignment.submission_dicts("foo"), key=lambda x: x["id"])
    b = sorted([x.to_dict() for x in assignment.find_assignment("foo").submissions], key=lambda x: x["id"])
    assert a == b

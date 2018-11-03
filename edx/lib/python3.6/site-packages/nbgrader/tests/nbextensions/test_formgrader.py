import pytest
import os
import shutil
import sys
import glob

from os.path import join

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from .. import run_nbgrader
from ...api import Gradebook, MissingEntry
from . import formgrade_utils as utils
from .conftest import notwindows, _make_nbserver, _make_browser, _close_nbserver, _close_browser
from ...utils import rmtree


if sys.platform == 'win32':
    tz = "Coordinated Universal Time"
else:
    tz = "UTC"


@pytest.fixture(scope="module")
def nbserver(request, port, tempdir, jupyter_config_dir, jupyter_data_dir, exchange, cache):
    server = _make_nbserver("course101", port, tempdir, jupyter_config_dir, jupyter_data_dir, exchange, cache)

    def fin():
        _close_nbserver(server)
    request.addfinalizer(fin)

    return server


@pytest.fixture
def browser(request, tempdir, nbserver):
    browser = _make_browser(tempdir)

    def fin():
        _close_browser(browser)
    request.addfinalizer(fin)

    return browser


@pytest.fixture(scope="module")
def gradebook(request, tempdir, nbserver):
    # copy files from the user guide
    source_path = join(os.path.dirname(__file__), "..", "..", "docs", "source", "user_guide", "source")
    submitted_path = join(os.path.dirname(__file__), "..", "..", "docs", "source", "user_guide", "submitted")

    shutil.copytree(source_path, "source")
    for student in ["bitdiddle", "hacker"]:
        shutil.copytree(join(submitted_path, student), join("submitted", student))

    # rename to old names -- we do this rather than changing all the tests
    # because I want the tests to operate on files with spaces in the names
    os.rename(join("source", "ps1"), join("source", "Problem Set 1"))
    os.rename(join("source", "Problem Set 1", "problem1.ipynb"), join("source", "Problem Set 1", "Problem 1.ipynb"))
    os.rename(join("source", "Problem Set 1", "problem2.ipynb"), join("source", "Problem Set 1", "Problem 2.ipynb"))
    os.rename(join("submitted", "bitdiddle"), join("submitted", "Bitdiddle"))
    os.rename(join("submitted", "Bitdiddle", "ps1"), join("submitted", "Bitdiddle", "Problem Set 1"))
    os.rename(join("submitted", "Bitdiddle", "Problem Set 1", "problem1.ipynb"), join("submitted", "Bitdiddle", "Problem Set 1", "Problem 1.ipynb"))
    os.rename(join("submitted", "Bitdiddle", "Problem Set 1", "problem2.ipynb"), join("submitted", "Bitdiddle", "Problem Set 1", "Problem 2.ipynb"))
    os.rename(join("submitted", "hacker"), join("submitted", "Hacker"))
    os.rename(join("submitted", "Hacker", "ps1"), join("submitted", "Hacker", "Problem Set 1"))
    os.rename(join("submitted", "Hacker", "Problem Set 1", "problem1.ipynb"), join("submitted", "Hacker", "Problem Set 1", "Problem 1.ipynb"))
    os.rename(join("submitted", "Hacker", "Problem Set 1", "problem2.ipynb"), join("submitted", "Hacker", "Problem Set 1", "Problem 2.ipynb"))

    # run nbgrader assign
    run_nbgrader([
        "assign", "Problem Set 1",
        "--IncludeHeaderFooter.header={}".format(join("source", "header.ipynb"))
    ])

    # run the autograder
    run_nbgrader(["autograde", "Problem Set 1"])

    # make sure louis is in the database (won't get added because he hasn't submitted anything!)
    run_nbgrader(["db", "student", "add", "Reasoner", "--first-name", "Louis", "--last-name", "R"])

    gb = Gradebook("sqlite:///gradebook.db")

    def fin():
        gb.close()
    request.addfinalizer(fin)

    return gb


@pytest.mark.nbextensions
def test_load_manage_assignments(browser, port, gradebook):
    # load the main page and make sure it is the Assignments page
    utils._get(browser, utils._formgrade_url(port))
    utils._wait_for_gradebook_page(browser, port, "")
    utils._check_breadcrumbs(browser, "Assignments")

    # click on the "Problem Set 1" link
    utils._click_link(browser, "Problem Set 1")
    browser.switch_to_window(browser.window_handles[1])
    utils._wait_for_tree_page(
        browser, port,
        utils._tree_url(port, "source/Problem Set 1"))
    browser.close()
    browser.switch_to_window(browser.window_handles[0])

    # click on the preview link
    browser.find_element_by_css_selector("td.preview .glyphicon").click()
    browser.switch_to_window(browser.window_handles[1])
    utils._wait_for_tree_page(
        browser, port,
        utils._tree_url(port, "release/Problem Set 1"))
    browser.close()
    browser.switch_to_window(browser.window_handles[0])

    # click on the number of submissions
    browser.find_element_by_css_selector("td.num-submissions a").click()
    utils._wait_for_gradebook_page(browser, port, "manage_submissions/Problem Set 1")


@pytest.mark.nbextensions
def test_load_manage_submissions(browser, port, gradebook):
    # load the submissions page
    utils._load_gradebook_page(browser, port, "manage_submissions/Problem Set 1")
    utils._check_breadcrumbs(browser, "Assignments", "Problem Set 1")

    # click on the "Assignments" link
    utils._click_link(browser, "Assignments")
    utils._wait_for_gradebook_page(browser, port, "manage_assignments")
    browser.back()

    # click on students
    for student in gradebook.students:
        try:
            gradebook.find_submission("Problem Set 1", student.id)
        except MissingEntry:
            continue

        utils._click_link(browser, "{}, {}".format(student.last_name, student.first_name))
        utils._wait_for_gradebook_page(browser, port, "manage_students/{}/Problem Set 1".format(student.id))
        browser.back()


@pytest.mark.nbextensions
def test_load_gradebook1(browser, port, gradebook):
    # load the assignments page
    utils._load_gradebook_page(browser, port, "gradebook")
    utils._check_breadcrumbs(browser, "Manual Grading")

    # click on the "Problem Set 1" link
    utils._click_link(browser, "Problem Set 1")
    utils._wait_for_gradebook_page(browser, port, "gradebook/Problem Set 1")


@pytest.mark.nbextensions
def test_load_gradebook2(browser, port, gradebook):
    utils._load_gradebook_page(browser, port, "gradebook/Problem Set 1")
    utils._check_breadcrumbs(browser, "Manual Grading", "Problem Set 1")

    # click the "Manual Grading" link
    utils._click_link(browser, "Manual Grading")
    utils._wait_for_gradebook_page(browser, port, "gradebook")
    browser.back()

    # click on the problem link
    for problem in gradebook.find_assignment("Problem Set 1").notebooks:
        utils._click_link(browser, problem.name)
        utils._wait_for_gradebook_page(browser, port, "gradebook/Problem Set 1/{}".format(problem.name))
        browser.back()


@pytest.mark.nbextensions
def test_load_gradebook3(browser, port, gradebook):
    for problem in gradebook.find_assignment("Problem Set 1").notebooks:
        utils._load_gradebook_page(browser, port, "gradebook/Problem Set 1/{}".format(problem.name))
        utils._check_breadcrumbs(browser, "Manual Grading", "Problem Set 1", problem.name)

        # click the "Manual Grading" link
        utils._click_link(browser, "Manual Grading")
        utils._wait_for_gradebook_page(browser, port, "gradebook")
        browser.back()

        # click the "Problem Set 1" link
        utils._click_link(browser, "Problem Set 1")
        utils._wait_for_gradebook_page(browser, port, "gradebook/Problem Set 1")
        browser.back()

        submissions = problem.submissions
        submissions.sort(key=lambda x: x.id)
        for i, submission in enumerate(submissions):
            # click on the "Submission #i" link
            utils._click_link(browser, "Submission #{}".format(i + 1))
            utils._wait_for_formgrader(browser, port, "submissions/{}/?index=0".format(submission.id))
            browser.back()


@pytest.mark.nbextensions
def test_gradebook3_show_hide_names(browser, port, gradebook):
    problem = gradebook.find_assignment("Problem Set 1").notebooks[0]
    utils._load_gradebook_page(browser, port, "gradebook/Problem Set 1/{}".format(problem.name))
    submissions = problem.submissions
    submissions.sort(key=lambda x: x.id)
    submission = submissions[0]

    top_elem = browser.find_elements_by_css_selector("tbody tr")[0]
    col1, col2 = top_elem.find_elements_by_css_selector("td")[:2]
    hidden = col1.find_element_by_css_selector(".glyphicon.name-hidden")
    shown = col1.find_element_by_css_selector(".glyphicon.name-shown")

    # check that the name is hidden
    assert col2.text == "Submission #1"
    assert not shown.is_displayed()
    assert hidden.is_displayed()

    # click the show icon
    hidden.click()

    # check that the name is shown
    assert col2.text == "{}, {}".format(submission.student.last_name, submission.student.first_name)
    assert shown.is_displayed()
    assert not hidden.is_displayed()

    # click the hide icon
    shown.click()

    # check that the name is hidden
    assert col2.text == "Submission #1"
    assert not shown.is_displayed()
    assert hidden.is_displayed()


@pytest.mark.nbextensions
def test_load_student1(browser, port, gradebook):
    # load the student view
    utils._load_gradebook_page(browser, port, "manage_students")
    utils._check_breadcrumbs(browser, "Students")

    # click on student
    for student in gradebook.students:
        utils._click_link(browser, "{}, {}".format(student.last_name, student.first_name))
        utils._wait_for_gradebook_page(browser, port, "manage_students/{}".format(student.id))
        browser.back()


@pytest.mark.nbextensions
def test_load_student2(browser, port, gradebook):
    for student in gradebook.students:
        utils._load_gradebook_page(browser, port, "manage_students/{}".format(student.id))
        utils._check_breadcrumbs(browser, "Students", student.id)
        try:
            submission = gradebook.find_submission("Problem Set 1", student.id)
        except MissingEntry:
            continue

        utils._click_link(browser, "Problem Set 1")
        utils._wait_for_gradebook_page(browser, port, "manage_students/{}/Problem Set 1".format(student.id))


@pytest.mark.nbextensions
def test_load_student3(browser, port, gradebook):
    for student in gradebook.students:
        try:
            submission = gradebook.find_submission("Problem Set 1", student.id)
        except MissingEntry:
            continue

        utils._load_gradebook_page(browser, port, "manage_students/{}/Problem Set 1".format(student.id))
        utils._check_breadcrumbs(browser, "Students", student.id, "Problem Set 1")

        for problem in gradebook.find_assignment("Problem Set 1").notebooks:
            submission = gradebook.find_submission_notebook(problem.name, "Problem Set 1", student.id)
            utils._click_link(browser, problem.name)
            utils._wait_for_formgrader(browser, port, "submissions/{}/?index=0".format(submission.id))
            browser.back()
            utils._wait_for_gradebook_page(browser, port, "manage_students/{}/Problem Set 1".format(student.id))


@pytest.mark.nbextensions
def test_switch_views(browser, port, gradebook):
    pages = ["", "manage_assignments", "gradebook", "manage_students"]
    links = [
        ("Manage Assignments", "manage_assignments"),
        ("Manual Grading", "gradebook"),
        ("Manage Students", "manage_students")
    ]

    for page in pages:
        utils._load_gradebook_page(browser, port, page)
        for link, target in links:
            utils._click_link(browser, link)
            utils._wait_for_gradebook_page(browser, port, target)
            browser.back()


@pytest.mark.nbextensions
def test_formgrade_view_breadcrumbs(browser, port, gradebook):
    for problem in gradebook.find_assignment("Problem Set 1").notebooks:
        submissions = problem.submissions
        submissions.sort(key=lambda x: x.id)

        for submission in submissions:
            utils._get(browser, utils._formgrade_url(port, "submissions/{}".format(submission.id)))
            utils._wait_for_formgrader(browser, port, "submissions/{}/?index=0".format(submission.id))

            # click on the "Manual Grading" link
            utils._click_link(browser, "Manual Grading")
            utils._wait_for_gradebook_page(browser, port, "gradebook")

            # go back
            browser.back()
            utils._wait_for_formgrader(browser, port, "submissions/{}/?index=0".format(submission.id))

            # click on the "Problem Set 1" link
            utils._click_link(browser, "Problem Set 1")
            utils._wait_for_gradebook_page(browser, port, "gradebook/Problem Set 1")

            # go back
            browser.back()
            utils._wait_for_formgrader(browser, port, "submissions/{}/?index=0".format(submission.id))

            # click on the problem link
            utils._click_link(browser, problem.name)
            utils._wait_for_gradebook_page(browser, port, "gradebook/Problem Set 1/{}".format(problem.name))

            # go back
            browser.back()
            utils._wait_for_formgrader(browser, port, "submissions/{}/?index=0".format(submission.id))


@pytest.mark.nbextensions
def test_load_live_notebook(browser, port, gradebook):
    for problem in gradebook.find_assignment("Problem Set 1").notebooks:
        submissions = problem.submissions
        submissions.sort(key=lambda x: x.id)

        for i, submission in enumerate(submissions):
            utils._get(browser, utils._formgrade_url(port, "submissions/{}".format(submission.id)))
            utils._wait_for_formgrader(browser, port, "submissions/{}/?index=0".format(submission.id))

            # check the live notebook link
            utils._click_link(browser, "Submission #{}".format(i + 1))
            browser.switch_to_window(browser.window_handles[1])
            utils._wait_for_notebook_page(
                browser, port,
                utils._notebook_url(
                    port, "autograded/{}/Problem Set 1/{}.ipynb".format(submission.student.id, problem.name)))
            browser.close()
            browser.switch_to_window(browser.window_handles[0])


@pytest.mark.nbextensions
def test_formgrade_images(browser, port, gradebook):
    submissions = gradebook.find_notebook("Problem 1", "Problem Set 1").submissions
    submissions.sort(key=lambda x: x.id)

    for submission in submissions:
        utils._get(browser, utils._formgrade_url(port, "submissions/{}".format(submission.id)))
        utils._wait_for_formgrader(browser, port, "submissions/{}/?index=0".format(submission.id))

        images = browser.find_elements_by_tag_name("img")
        for image in images:
            # check that the image is loaded, and that it has a width
            assert browser.execute_script("return arguments[0].complete", image)
            assert browser.execute_script("return arguments[0].naturalWidth", image) > 0


@pytest.mark.nbextensions
def test_next_prev_assignments(browser, port, gradebook):
    problem = gradebook.find_notebook("Problem 1", "Problem Set 1")
    submissions = problem.submissions
    submissions.sort(key=lambda x: x.id)

    # test navigating both with the arrow keys and with clicking the
    # next/previous links
    next_functions = [
        (utils._send_keys_to_body, browser, Keys.CONTROL, "."),
        (utils._click_element, browser, ".next a")
    ]
    prev_functions = [
        (utils._send_keys_to_body, browser, Keys.CONTROL, ","),
        (utils._click_element, browser, ".previous a")
    ]

    for n, p in zip(next_functions, prev_functions):
        # first element is the function, the other elements are the arguments
        # to that function
        next_function = lambda: n[0](*n[1:])
        prev_function = lambda: p[0](*p[1:])

        # Load the first submission
        utils._get(browser, utils._formgrade_url(port, "submissions/{}".format(submissions[0].id)))
        utils._wait_for_formgrader(browser, port, "submissions/{}/?index=0".format(submissions[0].id))

        # Move to the next submission
        next_function()
        utils._wait_for_formgrader(browser, port, "submissions/{}/?index=0".format(submissions[1].id))

        # Move to the next submission (should return to notebook list)
        next_function()
        utils._wait_for_gradebook_page(browser, port, "gradebook/Problem Set 1/Problem 1")

        # Go back
        browser.back()
        utils._wait_for_formgrader(browser, port, "submissions/{}/?index=0".format(submissions[1].id))

        # Move to the previous submission
        prev_function()
        utils._wait_for_formgrader(browser, port, "submissions/{}/?index=0".format(submissions[0].id))

        # Move to the previous submission (should return to the notebook list)
        prev_function()
        utils._wait_for_gradebook_page(browser, port, "gradebook/Problem Set 1/Problem 1")


@pytest.mark.nbextensions
def test_next_prev_failed_assignments(browser, port, gradebook):
    problem = gradebook.find_notebook("Problem 1", "Problem Set 1")
    submissions = problem.submissions
    submissions.sort(key=lambda x: x.id)

    # verify that we have the right number of submissions, and that one
    # failed tests and the other didn't
    assert len(submissions) == 2
    if submissions[0].failed_tests:
        assert not submissions[1].failed_tests
    else:
        assert submissions[1].failed_tests

    # Load the first submission
    utils._get(browser, utils._formgrade_url(port, "submissions/{}".format(submissions[0].id)))
    utils._wait_for_formgrader(browser, port, "submissions/{}/?index=0".format(submissions[0].id))

    if submissions[0].failed_tests:
        # Go to the next failed submission (should return to the notebook list)
        utils._send_keys_to_body(browser, Keys.CONTROL, Keys.SHIFT, ".")
        utils._wait_for_gradebook_page(browser, port, "gradebook/Problem Set 1/Problem 1")

        # Go back
        browser.back()
        utils._wait_for_formgrader(browser, port, "submissions/{}/?index=0".format(submissions[0].id))

        # Go to the previous failed submission (should return to the notebook list)
        utils._send_keys_to_body(browser, Keys.CONTROL, Keys.SHIFT, ",")
        utils._wait_for_gradebook_page(browser, port, "gradebook/Problem Set 1/Problem 1")

        # Go back
        browser.back()
        utils._wait_for_formgrader(browser, port, "submissions/{}/?index=0".format(submissions[0].id))

        # Go to the other notebook
        utils._send_keys_to_body(browser, Keys.CONTROL, ".")
        utils._wait_for_formgrader(browser, port, "submissions/{}/?index=0".format(submissions[1].id))

        # Go to the next failed submission (should return to the notebook list)
        utils._send_keys_to_body(browser, Keys.CONTROL, Keys.SHIFT, ".")
        utils._wait_for_gradebook_page(browser, port, "gradebook/Problem Set 1/Problem 1")

        # Go back
        browser.back()
        utils._wait_for_formgrader(browser, port, "submissions/{}/?index=0".format(submissions[1].id))

        # Go to the previous failed submission
        utils._send_keys_to_body(browser, Keys.CONTROL, Keys.SHIFT, ",")
        utils._wait_for_formgrader(browser, port, "submissions/{}/?index=0".format(submissions[0].id))

    else:
        # Go to the next failed submission
        utils._send_keys_to_body(browser, Keys.CONTROL, Keys.SHIFT, ".")
        utils._wait_for_formgrader(browser, port, "submissions/{}/?index=0".format(submissions[1].id))

        # Go back
        browser.back()
        utils._wait_for_formgrader(browser, port, "submissions/{}/?index=0".format(submissions[0].id))

        # Go to the previous failed submission (should return to the notebook list)
        utils._send_keys_to_body(browser, Keys.CONTROL, Keys.SHIFT, ",")
        utils._wait_for_gradebook_page(browser, port, "gradebook/Problem Set 1/Problem 1")

        # Go back
        browser.back()
        utils._wait_for_formgrader(browser, port, "submissions/{}/?index=0".format(submissions[0].id))

        # Go to the other notebook
        utils._send_keys_to_body(browser, Keys.CONTROL, ".")
        utils._wait_for_formgrader(browser, port, "submissions/{}/?index=0".format(submissions[1].id))

        # Go to the next failed submission (should return to the notebook list)
        utils._send_keys_to_body(browser, Keys.CONTROL, Keys.SHIFT, ".")
        utils._wait_for_gradebook_page(browser, port, "gradebook/Problem Set 1/Problem 1")

        # Go back
        browser.back()
        utils._wait_for_formgrader(browser, port, "submissions/{}/?index=0".format(submissions[1].id))

        # Go to the previous failed submission (should return to the notebook list)
        utils._send_keys_to_body(browser, Keys.CONTROL, Keys.SHIFT, ",")
        utils._wait_for_gradebook_page(browser, port, "gradebook/Problem Set 1/Problem 1")


@pytest.mark.nbextensions
def test_tabbing(browser, port, gradebook):
    utils._load_formgrade(browser, port, gradebook)

    # check that the next arrow is selected
    assert utils._get_active_element(browser) == utils._get_next_arrow(browser)
    assert utils._get_index(browser) == 0

    # check that the first comment box is selected
    utils._send_keys_to_body(browser, Keys.TAB)
    assert utils._get_active_element(browser) == utils._get_comment_box(browser, 0)
    assert utils._get_index(browser) == 1

    # tab to the next and check that the first points is selected
    utils._send_keys_to_body(browser, Keys.TAB)
    assert utils._get_active_element(browser) == utils._get_score_box(browser, 0)
    assert utils._get_index(browser) == 2

    # tab to the next and check that the first extra credit is selected
    utils._send_keys_to_body(browser, Keys.TAB)
    assert utils._get_active_element(browser) == utils._get_extra_credit_box(browser, 0)
    assert utils._get_index(browser) == 3

    # tab to the next and check that the second points is selected
    utils._send_keys_to_body(browser, Keys.TAB)
    assert utils._get_active_element(browser) == utils._get_score_box(browser, 1)
    assert utils._get_index(browser) == 4

    # tab to the next and check that the second extra credit is selected
    utils._send_keys_to_body(browser, Keys.TAB)
    assert utils._get_active_element(browser) == utils._get_extra_credit_box(browser, 1)
    assert utils._get_index(browser) == 5

    # tab to the next and check that the second comment is selected
    utils._send_keys_to_body(browser, Keys.TAB)
    assert utils._get_active_element(browser) == utils._get_comment_box(browser, 1)
    assert utils._get_index(browser) == 6

    # tab to the next and check that the third points is selected
    utils._send_keys_to_body(browser, Keys.TAB)
    assert utils._get_active_element(browser) == utils._get_score_box(browser, 2)
    assert utils._get_index(browser) == 7

    # tab to the next and check that the third extra credit is selected
    utils._send_keys_to_body(browser, Keys.TAB)
    assert utils._get_active_element(browser) == utils._get_extra_credit_box(browser, 2)
    assert utils._get_index(browser) == 8

    # tab to the next and check that the fourth points is selected
    utils._send_keys_to_body(browser, Keys.TAB)
    assert utils._get_active_element(browser) == utils._get_score_box(browser, 3)
    assert utils._get_index(browser) == 9

    # tab to the next and check that the fourth extra credit is selected
    utils._send_keys_to_body(browser, Keys.TAB)
    assert utils._get_active_element(browser) == utils._get_extra_credit_box(browser, 3)
    assert utils._get_index(browser) == 10

    # tab to the next and check that the fifth points is selected
    utils._send_keys_to_body(browser, Keys.TAB)
    assert utils._get_active_element(browser) == utils._get_score_box(browser, 4)
    assert utils._get_index(browser) == 11

    # tab to the next and check that the fifth extra credit is selected
    utils._send_keys_to_body(browser, Keys.TAB)
    assert utils._get_active_element(browser) == utils._get_extra_credit_box(browser, 4)
    assert utils._get_index(browser) == 12

    # tab to the next and check that the third comment is selected
    utils._send_keys_to_body(browser, Keys.TAB)
    assert utils._get_active_element(browser) == utils._get_comment_box(browser, 2)
    assert utils._get_index(browser) == 13

    # tab to the next and check that the sixth points is selected
    utils._send_keys_to_body(browser, Keys.TAB)
    assert utils._get_active_element(browser) == utils._get_score_box(browser, 5)
    assert utils._get_index(browser) == 14

    # tab to the next and check that the sixth extra credit is selected
    utils._send_keys_to_body(browser, Keys.TAB)
    assert utils._get_active_element(browser) == utils._get_extra_credit_box(browser, 5)
    assert utils._get_index(browser) == 15

    # tab to the next and check that the fourth comment is selected
    utils._send_keys_to_body(browser, Keys.TAB)
    assert utils._get_active_element(browser) == utils._get_comment_box(browser, 3)
    assert utils._get_index(browser) == 16

    # tab to the next and check that the next arrow is selected
    utils._send_keys_to_body(browser, Keys.TAB)
    assert utils._get_active_element(browser) == utils._get_next_arrow(browser)
    assert utils._get_index(browser) == 0



@pytest.mark.nbextensions
@pytest.mark.parametrize("index", range(4))
def test_save_comment(browser, port, gradebook, index):
    utils._load_formgrade(browser, port, gradebook)
    elem = utils._get_comment_box(browser, index)

    if elem.get_attribute("value") != "":
        elem.click()
        elem.clear()
        utils._save_comment(browser, index)
        utils._load_formgrade(browser, port, gradebook)
        elem = utils._get_comment_box(browser, index)
        assert elem.get_attribute("value") == ""

    elem.click()
    elem.send_keys("this comment has index {}".format(index))
    elem.send_keys(Keys.ENTER)
    elem.send_keys("blah blah blah")
    utils._save_comment(browser, index)

    utils._load_formgrade(browser, port, gradebook)
    elem = utils._get_comment_box(browser, index)
    assert elem.get_attribute("value") == "this comment has index {}\nblah blah blah".format(index)



@pytest.mark.nbextensions
@pytest.mark.parametrize("index", range(6))
def test_save_score(browser, port, gradebook, index):
    utils._load_formgrade(browser, port, gradebook)
    elem = utils._get_score_box(browser, index)

    if elem.get_attribute("value") != "":
        elem.click()
        elem.clear()
        utils._save_score(browser, index)
        utils._load_formgrade(browser, port, gradebook)
        elem = utils._get_score_box(browser, index)
        assert elem.get_attribute("value") == ""

    # check whether it needs manual grading
    if elem.get_attribute("placeholder") != "":
        assert not utils._get_needs_manual_grade(browser, elem.get_attribute("id"))
        assert "needs_manual_grade" not in elem.get_attribute("class").split(" ")
    else:
        assert utils._get_needs_manual_grade(browser, elem.get_attribute("id"))
        assert "needs_manual_grade" in elem.get_attribute("class").split(" ")

    # set the grade
    elem.click()
    elem.send_keys("{}".format((index + 1) / 10.0))
    utils._save_score(browser, index)
    utils._load_formgrade(browser, port, gradebook)
    elem = utils._get_score_box(browser, index)
    assert elem.get_attribute("value") == "{}".format((index + 1) / 10.0)

    # check whether it needs manual grading
    assert not utils._get_needs_manual_grade(browser, elem.get_attribute("id"))
    assert "needs_manual_grade" not in elem.get_attribute("class").split(" ")

    # clear the grade
    elem.click()
    elem.clear()
    utils._save_score(browser, index)
    utils._load_formgrade(browser, port, gradebook)
    elem = utils._get_score_box(browser, index)
    assert elem.get_attribute("value") == ""

    # check whether it needs manual grading
    if elem.get_attribute("placeholder") != "":
        assert not utils._get_needs_manual_grade(browser, elem.get_attribute("id"))
        assert "needs_manual_grade" not in elem.get_attribute("class").split(" ")
    else:
        assert utils._get_needs_manual_grade(browser, elem.get_attribute("id"))
        assert "needs_manual_grade" in elem.get_attribute("class").split(" ")


@pytest.mark.nbextensions
@pytest.mark.parametrize("index", range(6))
def test_save_extra_credit(browser, port, gradebook, index):
    utils._load_formgrade(browser, port, gradebook)
    elem = utils._get_extra_credit_box(browser, index)

    if elem.get_attribute("value") != "":
        elem.click()
        elem.clear()
        utils._save_score(browser, index)
        utils._load_formgrade(browser, port, gradebook)
        elem = utils._get_extra_credit_box(browser, index)
        assert elem.get_attribute("value") == ""

    # set the grade
    elem.click()
    elem.send_keys("{}".format((index + 1) / 10.0))
    utils._save_score(browser, index)
    utils._load_formgrade(browser, port, gradebook)
    elem = utils._get_extra_credit_box(browser, index)
    assert elem.get_attribute("value") == "{}".format((index + 1) / 10.0)

    # clear the grade
    elem.click()
    elem.clear()
    utils._save_score(browser, index)
    utils._load_formgrade(browser, port, gradebook)
    elem = utils._get_extra_credit_box(browser, index)
    assert elem.get_attribute("value") == ""


@pytest.mark.nbextensions
def test_same_part_navigation(browser, port, gradebook):
    problem = gradebook.find_notebook("Problem 1", "Problem Set 1")
    submissions = problem.submissions
    submissions.sort(key=lambda x: x.id)

    # Load the first submission
    utils._get(browser, utils._formgrade_url(port, "submissions/{}".format(submissions[0].id)))
    utils._wait_for_formgrader(browser, port, "submissions/{}/?index=0".format(submissions[0].id))

    # Click the second comment box and navigate to the next submission
    utils._get_comment_box(browser, 1).click()
    utils._send_keys_to_body(browser, Keys.CONTROL, ".")
    utils._wait_for_formgrader(browser, port, "submissions/{}/?index=6".format(submissions[1].id))
    assert utils._get_active_element(browser) == utils._get_comment_box(browser, 1)

    # Click the third score box and navigate to the previous submission
    utils._get_score_box(browser, 2).click()
    utils._send_keys_to_body(browser, Keys.CONTROL, ",")
    utils._wait_for_formgrader(browser, port, "submissions/{}/?index=7".format(submissions[0].id))
    assert utils._get_active_element(browser) == utils._get_score_box(browser, 2)

    # Click the third comment box and navigate to the next submission
    utils._get_comment_box(browser, 2).click()
    utils._send_keys_to_body(browser, Keys.CONTROL, ".")
    utils._wait_for_formgrader(browser, port, "submissions/{}/?index=11".format(submissions[1].id))
    assert utils._get_active_element(browser) == utils._get_score_box(browser, 4)

    # Navigate to the previous submission
    utils._send_keys_to_body(browser, Keys.CONTROL, ",")
    utils._wait_for_formgrader(browser, port, "submissions/{}/?index=11".format(submissions[0].id))
    assert utils._get_active_element(browser) == utils._get_score_box(browser, 4)


@pytest.mark.nbextensions
def test_keyboard_help(browser, port, gradebook):
    utils._load_formgrade(browser, port, gradebook)

    # show the help dialog
    utils._click_element(browser, ".help")
    utils._wait_for_element(browser, "help-dialog")
    WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#help-dialog button.btn-primary")))

    # close it
    utils._click_element(browser, "#help-dialog button.btn-primary")
    modal_not_present = lambda browser: browser.execute_script("""return $("#help-dialog").length === 0;""")
    WebDriverWait(browser, 10).until(modal_not_present)


@pytest.mark.nbextensions
def test_flag(browser, port, gradebook):
    utils._load_formgrade(browser, port, gradebook)

    # mark as flagged
    assert utils._flag(browser) == "Submission flagged"

    # mark as unflagged
    assert utils._flag(browser) == "Submission unflagged"

    # mark as flagged
    assert utils._flag(browser) == "Submission flagged"

    # mark as unflagged
    assert utils._flag(browser) == "Submission unflagged"


@pytest.mark.nbextensions
def test_formgrade_show_hide_names(browser, port, gradebook):
    utils._load_formgrade(browser, port, gradebook)

    problem = gradebook.find_notebook("Problem 1", "Problem Set 1")
    submissions = problem.submissions
    submissions.sort(key=lambda x: x.id)
    submission = submissions[0]

    name = browser.find_elements_by_css_selector(".breadcrumb li")[-1]
    hidden = browser.find_element_by_css_selector(".glyphicon.name-hidden")
    shown = browser.find_element_by_css_selector(".glyphicon.name-shown")

    # check that the name is hidden
    assert name.text == "Submission #1"
    assert not shown.is_displayed()
    assert hidden.is_displayed()

    # click the show icon
    hidden.click()
    WebDriverWait(browser, 10).until_not(EC.presence_of_element_located((By.CSS_SELECTOR, ".tooltip")))

    # check that the name is shown
    assert name.text == "{}, {}".format(submission.student.last_name, submission.student.first_name)
    assert shown.is_displayed()
    assert not hidden.is_displayed()

    # click the hide icon
    shown.click()
    WebDriverWait(browser, 10).until_not(EC.presence_of_element_located((By.CSS_SELECTOR, ".tooltip")))

    # check that the name is hidden
    assert name.text == "Submission #1"
    assert not shown.is_displayed()
    assert hidden.is_displayed()


@pytest.mark.nbextensions
def test_before_add_new_assignment(browser, port, gradebook):
    utils._load_gradebook_page(browser, port, "")
    assert len(browser.find_elements_by_css_selector("tbody tr")) == 1


@pytest.mark.nbextensions
def test_add_new_assignment(browser, port, gradebook):
    utils._load_gradebook_page(browser, port, "")
    n = len(browser.find_elements_by_css_selector("tbody tr"))

    # click the "add new assignment" button
    utils._click_link(browser, "Add new assignment...")
    utils._wait_for_element(browser, "add-assignment-modal")
    WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#add-assignment-modal .save")))

    # set the name and dudedate
    elem = browser.find_element_by_css_selector("#add-assignment-modal .name")
    elem.click()
    elem.send_keys("ps2")
    elem = browser.find_element_by_css_selector("#add-assignment-modal .duedate")
    elem.click()
    elem.send_keys("2017-07-05T17:00")
    elem = browser.find_element_by_css_selector("#add-assignment-modal .timezone")
    elem.click()
    elem.send_keys("UTC")

    # click save and wait for the modal to close
    utils._click_element(browser, "#add-assignment-modal .save")
    modal_not_present = lambda browser: browser.execute_script("""return $("#add-assignment-modal").length === 0;""")
    WebDriverWait(browser, 10).until(modal_not_present)

    # wait until both rows are present
    rows_present = lambda browser: len(browser.find_elements_by_css_selector("tbody tr")) == (n + 1)
    WebDriverWait(browser, 10).until(rows_present)

    # check that the new row is correct
    row = browser.find_elements_by_css_selector("tbody tr")[1]
    assert row.find_element_by_css_selector(".name").text == "ps2"
    assert row.find_element_by_css_selector(".duedate").text == "2017-07-05 17:00:00 {}".format(tz)
    assert row.find_element_by_css_selector(".status").text == "draft"
    assert utils._child_exists(row, ".edit a")
    assert utils._child_exists(row, ".assign a")
    assert not utils._child_exists(row, ".preview a")
    assert not utils._child_exists(row, ".release a")
    assert not utils._child_exists(row, ".collect a")
    assert row.find_element_by_css_selector(".num-submissions").text == "0"

    # reload the page and make sure everything is still correct
    utils._load_gradebook_page(browser, port, "")
    row = browser.find_elements_by_css_selector("tbody tr")[1]
    assert row.find_element_by_css_selector(".name").text == "ps2"
    assert row.find_element_by_css_selector(".duedate").text == "2017-07-05 17:00:00 {}".format(tz)
    assert row.find_element_by_css_selector(".status").text == "draft"
    assert utils._child_exists(row, ".edit a")
    assert utils._child_exists(row, ".assign a")
    assert not utils._child_exists(row, ".preview a")
    assert not utils._child_exists(row, ".release a")
    assert not utils._child_exists(row, ".collect a")
    assert row.find_element_by_css_selector(".num-submissions").text == "0"


@pytest.mark.nbextensions
def test_edit_assignment(browser, port, gradebook):
    utils._load_gradebook_page(browser, port, "")

    # click on the edit button
    row = browser.find_elements_by_css_selector("tbody tr")[1]
    row.find_element_by_css_selector(".edit a").click()
    utils._wait_for_element(browser, "edit-assignment-modal")
    WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#edit-assignment-modal .save")))

    # modify the duedate
    elem = browser.find_element_by_css_selector("#edit-assignment-modal .modal-duedate")
    elem.clear()
    elem.click()
    elem.send_keys("2017-07-05T18:00")

    # click save and wait for the modal to close
    utils._click_element(browser, "#edit-assignment-modal .save")
    modal_not_present = lambda browser: browser.execute_script("""return $("#edit-assignment-modal").length === 0;""")
    WebDriverWait(browser, 10).until(modal_not_present)

    # check that the modified row is correct
    row = browser.find_elements_by_css_selector("tbody tr")[1]
    assert row.find_element_by_css_selector(".name").text == "ps2"
    assert row.find_element_by_css_selector(".duedate").text == "2017-07-05 18:00:00 {}".format(tz)
    assert row.find_element_by_css_selector(".status").text == "draft"
    assert utils._child_exists(row, ".edit a")
    assert utils._child_exists(row, ".assign a")
    assert not utils._child_exists(row, ".preview a")
    assert not utils._child_exists(row, ".release a")
    assert not utils._child_exists(row, ".collect a")
    assert row.find_element_by_css_selector(".num-submissions").text == "0"

    # reload the page and make sure everything is still correct
    utils._load_gradebook_page(browser, port, "")
    row = browser.find_elements_by_css_selector("tbody tr")[1]
    assert row.find_element_by_css_selector(".name").text == "ps2"
    assert row.find_element_by_css_selector(".duedate").text == "2017-07-05 18:00:00 {}".format(tz)
    assert row.find_element_by_css_selector(".status").text == "draft"
    assert utils._child_exists(row, ".edit a")
    assert utils._child_exists(row, ".assign a")
    assert not utils._child_exists(row, ".preview a")
    assert not utils._child_exists(row, ".release a")
    assert not utils._child_exists(row, ".collect a")
    assert row.find_element_by_css_selector(".num-submissions").text == "0"


@pytest.mark.nbextensions
def test_generate_assignment_fail(browser, port, gradebook):
    utils._load_gradebook_page(browser, port, "")

    # click on the generate button -- should produce an error because there
    # are no notebooks for ps2 yet
    row = browser.find_elements_by_css_selector("tbody tr")[1]
    row.find_element_by_css_selector(".assign a").click()
    utils._wait_for_element(browser, "error-modal")
    WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#error-modal .close")))
    utils._click_element(browser, "#error-modal .close")
    modal_not_present = lambda browser: browser.execute_script("""return $("#error-modal").length === 0;""")
    WebDriverWait(browser, 10).until(modal_not_present)


@pytest.mark.nbextensions
def test_generate_assignment_success(browser, port, gradebook):
    utils._load_gradebook_page(browser, port, "")

    # add a notebook for ps2
    source_path = join(os.path.dirname(__file__), "..", "..", "docs", "source", "user_guide", "source", "ps1", "problem1.ipynb")
    shutil.copy(source_path, join("source", "ps2", "Problem 1.ipynb"))

    # click on the generate button -- should now succeed
    row = browser.find_elements_by_css_selector("tbody tr")[1]
    row.find_element_by_css_selector(".assign a").click()
    utils._wait_for_element(browser, "success-modal")
    WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#success-modal .close")))
    utils._click_element(browser, "#success-modal .close")
    modal_not_present = lambda browser: browser.execute_script("""return $("#success-modal").length === 0;""")
    WebDriverWait(browser, 10).until(modal_not_present)

    # check that the modified row is correct
    row = browser.find_elements_by_css_selector("tbody tr")[1]
    assert row.find_element_by_css_selector(".name").text == "ps2"
    assert row.find_element_by_css_selector(".duedate").text == "2017-07-05 18:00:00 {}".format(tz)
    assert row.find_element_by_css_selector(".status").text == "draft"
    assert utils._child_exists(row, ".edit a")
    assert utils._child_exists(row, ".assign a")
    assert utils._child_exists(row, ".preview a")
    if sys.platform == 'win32':
        assert not utils._child_exists(row, ".release a")
    else:
        assert utils._child_exists(row, ".release a")
    assert not utils._child_exists(row, ".collect a")
    assert row.find_element_by_css_selector(".num-submissions").text == "0"

    # reload the page and make sure everything is still correct
    utils._load_gradebook_page(browser, port, "")
    row = browser.find_elements_by_css_selector("tbody tr")[1]
    assert row.find_element_by_css_selector(".name").text == "ps2"
    assert row.find_element_by_css_selector(".duedate").text == "2017-07-05 18:00:00 {}".format(tz)
    assert row.find_element_by_css_selector(".status").text == "draft"
    assert utils._child_exists(row, ".edit a")
    assert utils._child_exists(row, ".assign a")
    assert utils._child_exists(row, ".preview a")
    if sys.platform == 'win32':
        assert not utils._child_exists(row, ".release a")
    else:
        assert utils._child_exists(row, ".release a")
    assert not utils._child_exists(row, ".collect a")
    assert row.find_element_by_css_selector(".num-submissions").text == "0"


@notwindows
@pytest.mark.nbextensions
def test_release_assignment(browser, port, gradebook):
    utils._load_gradebook_page(browser, port, "")

    # click on the release button
    row = browser.find_elements_by_css_selector("tbody tr")[1]
    row.find_element_by_css_selector(".release a").click()
    utils._wait_for_element(browser, "success-modal")
    WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#success-modal .close")))
    utils._click_element(browser, "#success-modal .close")
    modal_not_present = lambda browser: browser.execute_script("""return $("#success-modal").length === 0;""")
    WebDriverWait(browser, 10).until(modal_not_present)

    # check that the modified row is correct
    row = browser.find_elements_by_css_selector("tbody tr")[1]
    assert row.find_element_by_css_selector(".name").text == "ps2"
    assert row.find_element_by_css_selector(".duedate").text == "2017-07-05 18:00:00 {}".format(tz)
    assert row.find_element_by_css_selector(".status").text == "released"
    assert utils._child_exists(row, ".edit a")
    assert utils._child_exists(row, ".assign a")
    assert utils._child_exists(row, ".preview a")
    assert utils._child_exists(row, ".release a")
    assert utils._child_exists(row, ".collect a")
    assert row.find_element_by_css_selector(".num-submissions").text == "0"

    # reload the page and make sure everything is still correct
    utils._load_gradebook_page(browser, port, "")
    row = browser.find_elements_by_css_selector("tbody tr")[1]
    assert row.find_element_by_css_selector(".name").text == "ps2"
    assert row.find_element_by_css_selector(".duedate").text == "2017-07-05 18:00:00 {}".format(tz)
    assert row.find_element_by_css_selector(".status").text == "released"
    assert utils._child_exists(row, ".edit a")
    assert utils._child_exists(row, ".assign a")
    assert utils._child_exists(row, ".preview a")
    assert utils._child_exists(row, ".release a")
    assert utils._child_exists(row, ".collect a")
    assert row.find_element_by_css_selector(".num-submissions").text == "0"


@notwindows
@pytest.mark.nbextensions
def test_collect_assignment(browser, port, gradebook):
    run_nbgrader(["fetch", "ps2"])
    run_nbgrader(["submit", "ps2"])
    rmtree("ps2")

    utils._load_gradebook_page(browser, port, "")

    # click on the collect button
    row = browser.find_elements_by_css_selector("tbody tr")[1]
    row.find_element_by_css_selector(".collect a").click()
    utils._wait_for_element(browser, "success-modal")
    WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#success-modal .close")))
    utils._click_element(browser, "#success-modal .close")
    modal_not_present = lambda browser: browser.execute_script("""return $("#success-modal").length === 0;""")
    WebDriverWait(browser, 10).until(modal_not_present)

    # check that the modified row is correct
    row = browser.find_elements_by_css_selector("tbody tr")[1]
    assert row.find_element_by_css_selector(".name").text == "ps2"
    assert row.find_element_by_css_selector(".duedate").text == "2017-07-05 18:00:00 {}".format(tz)
    assert row.find_element_by_css_selector(".status").text == "released"
    assert utils._child_exists(row, ".edit a")
    assert utils._child_exists(row, ".assign a")
    assert utils._child_exists(row, ".preview a")
    assert utils._child_exists(row, ".release a")
    assert utils._child_exists(row, ".collect a")
    assert row.find_element_by_css_selector(".num-submissions").text == "1"

    # reload the page and make sure everything is still correct
    utils._load_gradebook_page(browser, port, "")
    row = browser.find_elements_by_css_selector("tbody tr")[1]
    assert row.find_element_by_css_selector(".name").text == "ps2"
    assert row.find_element_by_css_selector(".duedate").text == "2017-07-05 18:00:00 {}".format(tz)
    assert row.find_element_by_css_selector(".status").text == "released"
    assert utils._child_exists(row, ".edit a")
    assert utils._child_exists(row, ".assign a")
    assert utils._child_exists(row, ".preview a")
    assert utils._child_exists(row, ".release a")
    assert utils._child_exists(row, ".collect a")
    assert row.find_element_by_css_selector(".num-submissions").text == "1"


@notwindows
@pytest.mark.nbextensions
def test_unrelease_assignment(browser, port, gradebook):
    utils._load_gradebook_page(browser, port, "")

    # click on the unrelease button
    row = browser.find_elements_by_css_selector("tbody tr")[1]
    row.find_element_by_css_selector(".release a").click()
    utils._wait_for_element(browser, "success-modal")
    WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#success-modal .close")))
    utils._click_element(browser, "#success-modal .close")
    modal_not_present = lambda browser: browser.execute_script("""return $("#success-modal").length === 0;""")
    WebDriverWait(browser, 10).until(modal_not_present)

    # check that the modified row is correct
    row = browser.find_elements_by_css_selector("tbody tr")[1]
    assert row.find_element_by_css_selector(".name").text == "ps2"
    assert row.find_element_by_css_selector(".duedate").text == "2017-07-05 18:00:00 {}".format(tz)
    assert row.find_element_by_css_selector(".status").text == "draft"
    assert utils._child_exists(row, ".edit a")
    assert utils._child_exists(row, ".assign a")
    assert utils._child_exists(row, ".preview a")
    assert utils._child_exists(row, ".release a")
    assert not utils._child_exists(row, ".collect a")
    assert row.find_element_by_css_selector(".num-submissions").text == "1"

    # reload the page and make sure everything is still correct
    utils._load_gradebook_page(browser, port, "")
    row = browser.find_elements_by_css_selector("tbody tr")[1]
    assert row.find_element_by_css_selector(".name").text == "ps2"
    assert row.find_element_by_css_selector(".duedate").text == "2017-07-05 18:00:00 {}".format(tz)
    assert row.find_element_by_css_selector(".status").text == "draft"
    assert utils._child_exists(row, ".edit a")
    assert utils._child_exists(row, ".assign a")
    assert utils._child_exists(row, ".preview a")
    assert utils._child_exists(row, ".release a")
    assert not utils._child_exists(row, ".collect a")
    assert row.find_element_by_css_selector(".num-submissions").text == "1"


@pytest.mark.nbextensions
def test_manually_collect_assignment(browser, port, gradebook):
    existing_submissions = glob.glob(join("submitted", "*", "ps2"))
    for dirname in existing_submissions:
        rmtree(dirname)
    dest = join("submitted", "Bitdiddle", "ps2")
    if not os.path.exists(os.path.dirname(dest)):
        os.makedirs(os.path.dirname(dest))
    shutil.copytree(join("release", "ps2"), dest)
    with open(join(dest, "timestamp.txt"), "w") as fh:
        fh.write("2017-07-05 18:05:21 UTC")

    utils._load_gradebook_page(browser, port, "")

    # check that the row is correct
    row = browser.find_elements_by_css_selector("tbody tr")[1]
    assert row.find_element_by_css_selector(".name").text == "ps2"
    assert row.find_element_by_css_selector(".duedate").text == "2017-07-05 18:00:00 {}".format(tz)
    assert row.find_element_by_css_selector(".status").text == "draft"
    assert utils._child_exists(row, ".edit a")
    assert utils._child_exists(row, ".assign a")
    assert utils._child_exists(row, ".preview a")
    if sys.platform == 'win32':
        assert not utils._child_exists(row, ".release a")
    else:
        assert utils._child_exists(row, ".release a")
    assert not utils._child_exists(row, ".collect a")
    assert row.find_element_by_css_selector(".num-submissions").text == "1"


@pytest.mark.nbextensions
def test_before_autograde_assignment(browser, port, gradebook):
    utils._load_gradebook_page(browser, port, "manage_submissions/ps2")

    # check the contents of the row before grading
    row = browser.find_elements_by_css_selector("tbody tr")[0]
    assert row.find_element_by_css_selector(".student-name").text == "B, Ben"
    assert row.find_element_by_css_selector(".student-id").text == "Bitdiddle"
    assert row.find_element_by_css_selector(".timestamp").text == "2017-07-05 18:05:21 {}".format(tz)
    assert row.find_element_by_css_selector(".status").text == "needs autograding"
    assert row.find_element_by_css_selector(".score").text == ""
    assert utils._child_exists(row, ".autograde a")


@pytest.mark.nbextensions
def test_autograde_assignment1(browser, port, gradebook):
    utils._load_gradebook_page(browser, port, "manage_submissions/ps2")

    # click on the autograde button
    row = browser.find_elements_by_css_selector("tbody tr")[0]
    row.find_element_by_css_selector(".autograde a").click()
    utils._wait_for_element(browser, "success-modal")
    WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#success-modal .close")))
    utils._click_element(browser, "#success-modal .close")
    modal_not_present = lambda browser: browser.execute_script("""return $("#success-modal").length === 0;""")
    WebDriverWait(browser, 10).until(modal_not_present)

    # check that the modified row is correct
    row = browser.find_elements_by_css_selector("tbody tr")[0]
    assert row.find_element_by_css_selector(".student-name").text == "B, Ben"
    assert row.find_element_by_css_selector(".student-id").text == "Bitdiddle"
    assert row.find_element_by_css_selector(".timestamp").text == "2017-07-05 18:05:21 {}".format(tz)
    assert row.find_element_by_css_selector(".status").text == "graded"
    assert row.find_element_by_css_selector(".score").text == "0 / 6"
    assert utils._child_exists(row, ".autograde a")

    # refresh and check again
    utils._load_gradebook_page(browser, port, "manage_submissions/ps2")
    row = browser.find_elements_by_css_selector("tbody tr")[0]
    assert row.find_element_by_css_selector(".student-name").text == "B, Ben"
    assert row.find_element_by_css_selector(".student-id").text == "Bitdiddle"
    assert row.find_element_by_css_selector(".timestamp").text == "2017-07-05 18:05:21 {}".format(tz)
    assert row.find_element_by_css_selector(".status").text == "graded"
    assert row.find_element_by_css_selector(".score").text == "0 / 6"
    assert utils._child_exists(row, ".autograde a")


@pytest.mark.nbextensions
def test_autograde_assignment2(browser, port, gradebook):
    utils._load_gradebook_page(browser, port, "manage_submissions/ps2")

    # overwrite the file
    source_path = join(os.path.dirname(__file__), "..", "..", "docs", "source", "user_guide", "source", "ps1", "problem1.ipynb")
    shutil.copy(source_path, join("submitted", "Bitdiddle", "ps2", "Problem 1.ipynb"))

    # click on the autograde button
    row = browser.find_elements_by_css_selector("tbody tr")[0]
    row.find_element_by_css_selector(".autograde a").click()
    utils._wait_for_element(browser, "success-modal")
    WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#success-modal .close")))
    utils._click_element(browser, "#success-modal .close")
    modal_not_present = lambda browser: browser.execute_script("""return $("#success-modal").length === 0;""")
    WebDriverWait(browser, 10).until(modal_not_present)

    # check that the modified row is correct
    row = browser.find_elements_by_css_selector("tbody tr")[0]
    assert row.find_element_by_css_selector(".student-name").text == "B, Ben"
    assert row.find_element_by_css_selector(".student-id").text == "Bitdiddle"
    assert row.find_element_by_css_selector(".timestamp").text == "2017-07-05 18:05:21 {}".format(tz)
    assert row.find_element_by_css_selector(".status").text == "needs manual grading"
    assert row.find_element_by_css_selector(".score").text == "3 / 6"
    assert utils._child_exists(row, ".autograde a")

    # refresh and check again
    utils._load_gradebook_page(browser, port, "manage_submissions/ps2")
    row = browser.find_elements_by_css_selector("tbody tr")[0]
    assert row.find_element_by_css_selector(".student-name").text == "B, Ben"
    assert row.find_element_by_css_selector(".student-id").text == "Bitdiddle"
    assert row.find_element_by_css_selector(".timestamp").text == "2017-07-05 18:05:21 {}".format(tz)
    assert row.find_element_by_css_selector(".status").text == "needs manual grading"
    assert row.find_element_by_css_selector(".score").text == "3 / 6"
    assert utils._child_exists(row, ".autograde a")


@pytest.mark.nbextensions
def test_before_add_new_student(browser, port, gradebook):
    utils._load_gradebook_page(browser, port, "manage_students")
    assert len(browser.find_elements_by_css_selector("tbody tr")) == 3


@pytest.mark.nbextensions
def test_add_new_student(browser, port, gradebook):
    utils._load_gradebook_page(browser, port, "manage_students")
    n = len(browser.find_elements_by_css_selector("tbody tr"))

    # click the "add new assignment" button
    utils._click_link(browser, "Add new student...")
    utils._wait_for_element(browser, "add-student-modal")
    WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#add-student-modal .save")))

    # set the name and dudedate
    elem = browser.find_element_by_css_selector("#add-student-modal .id")
    elem.click()
    elem.send_keys("ator")
    elem = browser.find_element_by_css_selector("#add-student-modal .first-name")
    elem.click()
    elem.send_keys("Eva Lou")
    elem = browser.find_element_by_css_selector("#add-student-modal .last-name")
    elem.click()
    elem.send_keys("Ator")
    elem = browser.find_element_by_css_selector("#add-student-modal .email")
    elem.click()
    elem.send_keys("ela@email.com")

    # click save and wait for the modal to close
    utils._click_element(browser, "#add-student-modal .save")
    modal_not_present = lambda browser: browser.execute_script("""return $("#add-student-modal").length === 0;""")
    WebDriverWait(browser, 10).until(modal_not_present)

    # wait until both rows are present
    rows_present = lambda browser: len(browser.find_elements_by_css_selector("tbody tr")) == (n + 1)
    WebDriverWait(browser, 10).until(rows_present)

    # check that the new row is correct
    row = browser.find_elements_by_css_selector("tbody tr")[0]
    assert row.find_element_by_css_selector(".name").text == "Ator, Eva Lou"
    assert row.find_element_by_css_selector(".id").text == "ator"
    assert row.find_element_by_css_selector(".email").text == "ela@email.com"
    assert row.find_element_by_css_selector(".score").text == "0 / 15"
    assert utils._child_exists(row, ".edit a")

    # reload the page and make sure everything is still correct
    utils._load_gradebook_page(browser, port, "manage_students")
    row = browser.find_elements_by_css_selector("tbody tr")[0]
    assert row.find_element_by_css_selector(".name").text == "Ator, Eva Lou"
    assert row.find_element_by_css_selector(".id").text == "ator"
    assert row.find_element_by_css_selector(".email").text == "ela@email.com"
    assert row.find_element_by_css_selector(".score").text == "0 / 15"
    assert utils._child_exists(row, ".edit a")


@pytest.mark.nbextensions
def test_edit_student(browser, port, gradebook):
    utils._load_gradebook_page(browser, port, "manage_students")

    # click on the edit button
    row = browser.find_elements_by_css_selector("tbody tr")[0]
    row.find_element_by_css_selector(".edit a").click()
    utils._wait_for_element(browser, "edit-student-modal")
    WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#edit-student-modal .modal-email")))

    # modify the duedate
    elem = browser.find_element_by_css_selector("#edit-student-modal .modal-email")
    elem.clear()
    elem.click()
    elem.send_keys("ela@email.net")

    # click save and wait for the modal to close
    utils._click_element(browser, "#edit-student-modal .save")
    modal_not_present = lambda browser: browser.execute_script("""return $("#edit-student-modal").length === 0;""")
    WebDriverWait(browser, 10).until(modal_not_present)

    # check that the modified row is correct
    row = browser.find_elements_by_css_selector("tbody tr")[0]
    assert row.find_element_by_css_selector(".name").text == "Ator, Eva Lou"
    assert row.find_element_by_css_selector(".id").text == "ator"
    assert row.find_element_by_css_selector(".email").text == "ela@email.net"
    assert row.find_element_by_css_selector(".score").text == "0 / 15"
    assert utils._child_exists(row, ".edit a")

    # reload the page and make sure everything is still correct
    utils._load_gradebook_page(browser, port, "manage_students")
    row = browser.find_elements_by_css_selector("tbody tr")[0]
    assert row.find_element_by_css_selector(".name").text == "Ator, Eva Lou"
    assert row.find_element_by_css_selector(".id").text == "ator"
    assert row.find_element_by_css_selector(".email").text == "ela@email.net"
    assert row.find_element_by_css_selector(".score").text == "0 / 15"
    assert utils._child_exists(row, ".edit a")

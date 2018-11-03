import pytest

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .conftest import _make_nbserver, _make_browser, _close_nbserver, _close_browser


@pytest.fixture(scope="module")
def nbserver(request, port, tempdir, jupyter_config_dir, jupyter_data_dir, exchange, cache):
    server = _make_nbserver("", port, tempdir, jupyter_config_dir, jupyter_data_dir, exchange, cache)

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


def _wait(browser):
    return WebDriverWait(browser, 30)


def _load_notebook(browser, port, notebook, retries=5):
    # go to the correct page
    browser.get("http://localhost:{}/notebooks/{}".format(port, notebook))

    def page_loaded(browser):
        return browser.execute_script(
            'return typeof Jupyter !== "undefined" && Jupyter.page !== undefined;')

    # wait for the page to load
    try:
        _wait(browser).until(page_loaded)
    except TimeoutException:
        if retries > 0:
            print("Retrying page load...")
            # page timeout, but sometimes this happens, so try refreshing?
            _load_notebook(browser, port, retries=retries - 1)
        else:
            print("Failed to load the page too many times")
            raise


def _wait_for_validate_button(browser):
    _wait(browser).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "button.validate")))


def _wait_for_modal(browser):
    _wait(browser).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".modal-dialog")))


def _dismiss_modal(browser):
    button = browser.find_element_by_css_selector(".modal-footer .btn-primary")
    button.click()

    def modal_gone(browser):
        try:
            browser.find_element_by_css_selector(".modal-dialog")
        except NoSuchElementException:
            return True
        return False
    _wait(browser).until(modal_gone)


@pytest.mark.nbextensions
def test_validate_ok(browser, port):
    _load_notebook(browser, port, "submitted-changed.ipynb")
    _wait_for_validate_button(browser)

    # click the "validate" button
    browser.find_element_by_css_selector("button.validate").click()

    # wait for the modal dialog to appear
    _wait_for_modal(browser)

    # check that it succeeded
    browser.find_element_by_css_selector(".modal-dialog .validation-success")

    # close the modal dialog
    _dismiss_modal(browser)


@pytest.mark.nbextensions
def test_validate_failure(browser, port):
    _load_notebook(browser, port, "submitted-unchanged.ipynb")
    _wait_for_validate_button(browser)

    # click the "validate" button
    browser.find_element_by_css_selector("button.validate").click()

    # wait for the modal dialog to appear
    _wait_for_modal(browser)

    # check that it failed
    browser.find_element_by_css_selector(".modal-dialog .validation-failed")

    # close the modal dialog
    _dismiss_modal(browser)


@pytest.mark.nbextensions
def test_validate_grade_cell_changed(browser, port):
    _load_notebook(browser, port, "submitted-grade-cell-changed.ipynb")
    _wait_for_validate_button(browser)

    # click the "validate" button
    browser.find_element_by_css_selector("button.validate").click()

    # wait for the modal dialog to appear
    _wait_for_modal(browser)

    # check that it failed
    browser.find_element_by_css_selector(".modal-dialog .validation-changed")

    # close the modal dialog
    _dismiss_modal(browser)


@pytest.mark.nbextensions
def test_validate_locked_cell_changed(browser, port):
    _load_notebook(browser, port, "submitted-locked-cell-changed.ipynb")
    _wait_for_validate_button(browser)

    # click the "validate" button
    browser.find_element_by_css_selector("button.validate").click()

    # wait for the modal dialog to appear
    _wait_for_modal(browser)

    # check that it failed
    browser.find_element_by_css_selector(".modal-dialog .validation-changed")

    # close the modal dialog
    _dismiss_modal(browser)


@pytest.mark.nbextensions
def test_validate_open_relative_file(browser, port):
    _load_notebook(browser, port, "open_relative_file.ipynb")
    _wait_for_validate_button(browser)

    # click the "validate" button
    browser.find_element_by_css_selector("button.validate").click()

    # wait for the modal dialog to appear
    _wait_for_modal(browser)

    # check that it succeeded
    browser.find_element_by_css_selector(".modal-dialog .validation-success")

    # close the modal dialog
    _dismiss_modal(browser)

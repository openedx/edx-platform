from six.moves.urllib.parse import urljoin, unquote
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException



def _formgrade_url(port, url=""):
    return urljoin("http://localhost:{}/formgrader/".format(port), url).rstrip("/")


def _notebook_url(port, url=""):
    return urljoin("http://localhost:{}/notebooks/".format(port), url).rstrip("/")


def _tree_url(port, url=""):
    return urljoin("http://localhost:{}/tree/".format(port), url).rstrip("/")


def _check_url(browser, port, url):
    if not url.startswith("http"):
        url = _formgrade_url(port, url)
    assert unquote(browser.current_url).rstrip("/") == url


def _check_breadcrumbs(browser, *breadcrumbs):
    # check that breadcrumbs are correct
    elements = browser.find_elements_by_css_selector(".breadcrumb li")
    assert tuple([e.text for e in elements]) == breadcrumbs

    # check that the active breadcrumb is correct
    element = browser.find_element_by_css_selector(".breadcrumb li.active")
    assert element.text == breadcrumbs[-1]


def _click_link(browser, link_text, partial=False):
    if partial:
        element = browser.find_element_by_partial_link_text(link_text)
    else:
        element = browser.find_element_by_link_text(link_text)
    element.click()


def _wait_for_element(browser, element_id, time=10):
    return WebDriverWait(browser, time).until(
        EC.presence_of_element_located((By.ID, element_id))
    )


def _wait_for_visibility_of_element(browser, element_id, time=10):
    return WebDriverWait(browser, time).until(
        EC.visibility_of_element_located((By.ID, element_id))
    )


def _wait_for_gradebook_page(browser, port, url):
    page_loaded = lambda browser: browser.execute_script(
        """return typeof models !== "undefined" && models !== undefined && models.loaded === true;""")
    WebDriverWait(browser, 10).until(page_loaded)
    _check_url(browser, port, url)


def _get(browser, url, retries=5):
    try:
        browser.get(url)
        assert browser.get_cookies()
    except TimeoutException:
        if retries == 0:
            raise
        else:
            print("Failed to load '{}', trying again...".format(url))
            _get(browser, url, retries=retries - 1)


def _load_gradebook_page(browser, port, url):
    _get(browser, _formgrade_url(port, url))
    _wait_for_gradebook_page(browser, port, url)


def _wait_for_tree_page(browser, port, url):
    _wait_for_element(browser, "ipython-main-app")
    _check_url(browser, port, url)


def _wait_for_notebook_page(browser, port, url):
    _wait_for_element(browser, "notebook-container")
    _check_url(browser, port, url)


def _wait_for_formgrader(browser, port, url, retries=5):
    page_loaded = lambda browser: browser.execute_script(
        """
        if (!(typeof MathJax !== "undefined" && MathJax !== undefined && MathJax.loaded)) {
            return false;
        }

        if (!(typeof formgrader !== "undefined" && formgrader !== undefined)) {
            return false;
        }

        if (!(formgrader.grades !== undefined && formgrader.grades.loaded)) {
            return false;
        }

        if (!(formgrader.comments !== undefined && formgrader.comments.loaded)) {
            return false;
        }

        if (!(typeof autosize !== "undefined" && autosize !== undefined)) {
            return false;
        }

        return true;
        """)
    try:
        _wait_for_element(browser, "notebook-container")
        WebDriverWait(browser, 10).until(page_loaded)
    except TimeoutException:
        if retries == 0:
            raise
        else:
            print("Failed to load formgrader (url '{}'), trying again...".format(url))
            _get(browser, browser.current_url)
            _wait_for_formgrader(browser, port, url, retries=retries - 1)

    _check_url(browser, port, url)


def _click_element(browser, name):
    browser.find_element_by_css_selector(name).click()


def _send_keys_to_body(browser, *keys):
    body = browser.find_element_by_tag_name("body")
    body.send_keys(*keys)


def _get_next_arrow(browser):
    return browser.find_element_by_css_selector(".next a")


def _get_comment_box(browser, index):
    return browser.find_elements_by_css_selector(".comment")[index]


def _get_score_box(browser, index):
    return browser.find_elements_by_css_selector(".score")[index]


def _get_extra_credit_box(browser, index):
    return browser.find_elements_by_css_selector(".extra-credit")[index]


def _save_comment(browser, index):
    _send_keys_to_body(browser, Keys.ESCAPE)
    glyph = browser.find_elements_by_css_selector(".comment-saved")[index]
    WebDriverWait(browser, 10).until(lambda browser: glyph.is_displayed())
    WebDriverWait(browser, 10).until(lambda browser: not glyph.is_displayed())


def _save_score(browser, index):
    _send_keys_to_body(browser, Keys.ESCAPE)
    glyph = browser.find_elements_by_css_selector(".score-saved")[index]
    WebDriverWait(browser, 10).until(lambda browser: glyph.is_displayed())
    WebDriverWait(browser, 10).until(lambda browser: not glyph.is_displayed())


def _get_needs_manual_grade(browser, name):
    return browser.execute_script(
        'return formgrader.grades.findWhere({name: "%s"}).get("needs_manual_grade");' % name)


def _flag(browser):
    _send_keys_to_body(browser, Keys.SHIFT, Keys.CONTROL, "f")
    message = browser.find_element_by_id("statusmessage")
    WebDriverWait(browser, 10).until(lambda browser: message.is_displayed())
    WebDriverWait(browser, 10).until(lambda browser: not message.is_displayed())
    return browser.execute_script("return $('#statusmessage').text();")


def _get_active_element(browser):
    return browser.execute_script("return document.activeElement;")


def _get_index(browser):
    return browser.execute_script("return formgrader.getIndex(document.activeElement);")


def _load_formgrade(browser, port, gradebook):
    problem = gradebook.find_notebook("Problem 1", "Problem Set 1")
    submissions = problem.submissions
    submissions.sort(key=lambda x: x.id)

    _load_gradebook_page(browser, port, "gradebook/Problem Set 1/Problem 1")
    _click_link(browser, "Submission #1")
    _wait_for_formgrader(browser, port, "submissions/{}/?index=0".format(submissions[0].id))


def _child_exists(elem, selector):
    try:
        elem.find_element_by_css_selector(selector)
    except NoSuchElementException:
        return False
    else:
        return True

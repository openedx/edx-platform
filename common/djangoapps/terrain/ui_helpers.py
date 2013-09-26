#pylint: disable=C0111
#pylint: disable=W0621

from lettuce import world
import time
import platform
from urllib import quote_plus
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from lettuce.django import django_url
from nose.tools import assert_true  # pylint: disable=E0611


@world.absorb
def wait(seconds):
    time.sleep(float(seconds))


@world.absorb
def visit(url):
    world.browser.visit(django_url(url))


@world.absorb
def url_equals(url):
    return world.browser.url == django_url(url)


@world.absorb
def is_css_present(css_selector, wait_time=10):
    return world.browser.is_element_present_by_css(css_selector, wait_time=wait_time)


@world.absorb
def is_css_not_present(css_selector, wait_time=5):
    world.browser.driver.implicitly_wait(1)
    try:
        return world.browser.is_element_not_present_by_css(css_selector, wait_time=wait_time)
    except:
        raise
    finally:
        world.browser.driver.implicitly_wait(world.IMPLICIT_WAIT)

@world.absorb
def css_has_text(css_selector, text, index=0):
    return world.css_text(css_selector, index=index) == text


@world.absorb
def wait_for(func, timeout=5):
        WebDriverWait(
            driver=world.browser.driver,
            timeout=timeout,
            ignored_exceptions=(StaleElementReferenceException)
        ).until(func)


def wait_for_present(css_selector, timeout=30):
    """
    Waiting for the element to be present in the DOM.
    Throws an error if the WebDriverWait timeout clock expires.
    Otherwise this method will return None
    """
    try:
        WebDriverWait(
            driver=world.browser.driver,
            timeout=timeout,
            ignored_exceptions=(StaleElementReferenceException)
        ).until(EC.presence_of_element_located((By.CSS_SELECTOR, css_selector,)))
    except TimeoutException:
        raise TimeoutException("Timed out waiting for {} to be present.".format(css_selector))


@world.absorb
def wait_for_visible(css_selector, timeout=30):
    """
    Waiting for the element to be visible in the DOM.
    Throws an error if the WebDriverWait timeout clock expires.
    Otherwise this method will return None
    """
    try:
        WebDriverWait(
            driver=world.browser.driver,
            timeout=timeout,
            ignored_exceptions=(StaleElementReferenceException)
        ).until(EC.visibility_of_element_located((By.CSS_SELECTOR, css_selector,)))
    except TimeoutException:
        raise TimeoutException("Timed out waiting for {} to be visible.".format(css_selector))


@world.absorb
def wait_for_invisible(css_selector, timeout=30):
    """
    Waiting for the element to be either invisible or not present on the DOM.
    Throws an error if the WebDriverWait timeout clock expires.
    Otherwise this method will return None
    """
    try:
        WebDriverWait(
            driver=world.browser.driver,
            timeout=timeout,
            ignored_exceptions=(StaleElementReferenceException)
        ).until(EC.invisibility_of_element_located((By.CSS_SELECTOR, css_selector,)))
    except TimeoutException:
        raise TimeoutException("Timed out waiting for {} to be invisible.".format(css_selector))


@world.absorb
def wait_for_clickable(css_selector, timeout=30):
    """
    Waiting for the element to be present and clickable.
    Throws an error if the WebDriverWait timeout clock expires.
    Otherwise this method will return None.
    """
    # Sometimes the element is clickable then gets obscured.
    # In this case, pause so that it is not reported clickable too early
    try:
        WebDriverWait(
            driver=world.browser.driver,
            timeout=timeout,
            ignored_exceptions=(StaleElementReferenceException)
        ).until(EC.element_to_be_clickable((By.CSS_SELECTOR, css_selector,)))
    except TimeoutException:
        raise TimeoutException("Timed out waiting for {} to be clickable.".format(css_selector))


@world.absorb
def css_find(css, wait_time=30):
    """
    Wait for the element(s) as defined by css locator
    to be present.

    This method will return a WebDriverElement.
    """
    wait_for_present(css_selector=css, timeout=wait_time)
    return world.browser.find_by_css(css)


@world.absorb
def css_click(css_selector, index=0, wait_time=30):
    """
    Perform a click on a CSS selector, first waiting for the element
    to be present and clickable.

    This method will return True if the click worked.
    """
    wait_for_clickable(css_selector, timeout=wait_time)
    assert_true(world.css_find(css_selector)[index].visible,
                msg="Element {}[{}] is present but not visible".format(css_selector, index))

    # Sometimes you can't click in the center of the element, as
    # another element might be on top of it. In this case, try
    # clicking in the upper left corner.
    try:
        return retry_on_exception(lambda: world.css_find(css_selector)[index].click())

    except WebDriverException:
        return css_click_at(css_selector, index=index)


@world.absorb
def css_check(css_selector, index=0, wait_time=30):
    """
    Checks a check box based on a CSS selector, first waiting for the element
    to be present and clickable. This is just a wrapper for calling "click"
    because that's how selenium interacts with check boxes and radio buttons.

    This method will return True if the check worked.
    """
    return css_click(css_selector=css_selector, index=index, wait_time=wait_time)


@world.absorb
def css_click_at(css_selector, index=0, x_coord=10, y_coord=10, timeout=5):
    '''
    A method to click at x,y coordinates of the element
    rather than in the center of the element
    '''
    wait_for_clickable(css_selector, timeout=timeout)
    element = css_find(css_selector)[index]
    assert_true(element.visible,
                msg="Element {}[{}] is present but not visible".format(css_selector, index))

    element.action_chains.move_to_element_with_offset(element._element, x_coord, y_coord)
    element.action_chains.click()
    element.action_chains.perform()


@world.absorb
def select_option(name, value, index=0, wait_time=30):
    '''
    A method to select an option
    This method will return True if the selection worked.
    '''
    select_css = "select[name='{}']".format(name)
    option_css = "option[value='{}']".format(value)

    css_selector = "{} {}".format(select_css, option_css)
    return css_click(css_selector=css_selector, index=index, wait_time=wait_time)


@world.absorb
def id_click(elem_id):
    """
    Perform a click on an element as specified by its id
    """
    css_click('#{}'.format(elem_id))


@world.absorb
def css_fill(css_selector, text, index=0):
    retry_on_exception(lambda: css_find(css_selector)[index].fill(text))


@world.absorb
def click_link(partial_text, index=0):
    retry_on_exception(lambda: world.browser.find_link_by_partial_text(partial_text)[index].click())


@world.absorb
def css_text(css_selector, index=0, timeout=30):
    # Wait for the css selector to appear
    if is_css_present(css_selector):
        return retry_on_exception(lambda: css_find(css_selector, wait_time=timeout)[index].text)
    else:
        return ""


@world.absorb
def css_value(css_selector, index=0):
    # Wait for the css selector to appear
    if is_css_present(css_selector):
        return retry_on_exception(lambda: css_find(css_selector)[index].value)
    else:
        return ""


@world.absorb
def css_html(css_selector, index=0):
    """
    Returns the HTML of a css_selector
    """
    assert is_css_present(css_selector)
    return retry_on_exception(lambda: css_find(css_selector)[index].html)


@world.absorb
def css_has_class(css_selector, class_name, index=0):
    return retry_on_exception(lambda: css_find(css_selector)[index].has_class(class_name))


@world.absorb
def css_visible(css_selector, index=0):
    assert is_css_present(css_selector)
    return retry_on_exception(lambda: css_find(css_selector)[index].visible)


@world.absorb
def dialogs_closed():
    def are_dialogs_closed(_driver):
        '''
        Return True when no modal dialogs are visible
        '''
        return not css_visible('.modal')
    wait_for(are_dialogs_closed)
    return not css_visible('.modal')


@world.absorb
def save_the_html(path='/tmp'):
    url = world.browser.url
    html = world.browser.html.encode('ascii', 'ignore')
    filename = "{path}/{name}.html".format(path=path, name=quote_plus(url))
    with open(filename, "w") as f:
        f.write(html)


@world.absorb
def click_course_content():
    course_content_css = 'li.nav-course-courseware'
    world.css_click(course_content_css)


@world.absorb
def click_course_settings():
    course_settings_css = 'li.nav-course-settings'
    world.css_click(course_settings_css)


@world.absorb
def click_tools():
    tools_css = 'li.nav-course-tools'
    world.css_click(tools_css)


@world.absorb
def is_mac():
    return platform.mac_ver()[0] is not ''


@world.absorb
def is_firefox():
    return world.browser.driver_name is 'Firefox'


@world.absorb
def trigger_event(css_selector, event='change', index=0):
    world.browser.execute_script("$('{}:eq({})').trigger('{}')".format(css_selector, index, event))


@world.absorb
def retry_on_exception(func, max_attempts=5, ignored_exceptions=StaleElementReferenceException):
    """
    Retry the interaction, ignoring the passed exceptions.
    By default ignore StaleElementReferenceException, which happens often in our application
    when the DOM is being manipulated by client side JS.
    Note that ignored_exceptions is passed directly to the except block, and as such can be
    either a single exception or multiple exceptions as a parenthesized tuple.
    """
    attempt = 0
    while attempt < max_attempts:
        try:
            return func()
            break
        except ignored_exceptions:
            world.wait(1)
            attempt += 1

    assert_true(attempt < max_attempts, 'Ran out of attempts to execute {}'.format(func))

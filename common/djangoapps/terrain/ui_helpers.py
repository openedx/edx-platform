#pylint: disable=C0111
#pylint: disable=W0621

from lettuce import world
import time
import platform
from urllib import quote_plus
from selenium.common.exceptions import WebDriverException, StaleElementReferenceException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from lettuce.django import django_url
from nose.tools import assert_true


@world.absorb
def wait(seconds):
    time.sleep(float(seconds))


@world.absorb
def wait_for(func):
    WebDriverWait(world.browser.driver, 5).until(func)


@world.absorb
def visit(url):
    world.browser.visit(django_url(url))


@world.absorb
def url_equals(url):
    return world.browser.url == django_url(url)


@world.absorb
def is_css_present(css_selector, wait_time=5):
    return world.browser.is_element_present_by_css(css_selector, wait_time=wait_time)


@world.absorb
def is_css_not_present(css_selector, wait_time=5):
    return world.browser.is_element_not_present_by_css(css_selector, wait_time=wait_time)


@world.absorb
def css_has_text(css_selector, text):
    return world.css_text(css_selector) == text


@world.absorb
def css_find(css, wait_time=5):
    def is_visible(_driver):
        return EC.visibility_of_element_located((By.CSS_SELECTOR, css,))

    world.browser.is_element_present_by_css(css, wait_time=wait_time)
    wait_for(is_visible)
    return world.browser.find_by_css(css)


@world.absorb
def css_click(css_selector, index=0, max_attempts=5, success_condition=lambda: True):
    """
    Perform a click on a CSS selector, retrying if it initially fails.

    This function handles errors that may be thrown if the component cannot be clicked on.
    However, there are cases where an error may not be thrown, and yet the operation did not
    actually succeed. For those cases, a success_condition lambda can be supplied to verify that the click worked.

    This function will return True if the click worked (taking into account both errors and the optional
    success_condition).
    """
    assert is_css_present(css_selector), "{} is not present".format(css_selector)
    for _ in range(max_attempts):
        try:
            world.css_find(css_selector)[index].click()
            if success_condition():
                return
        except WebDriverException:
            # Occasionally, MathJax or other JavaScript can cover up
            # an element temporarily.
            # If this happens, wait a second, then try again
            world.wait(1)
        except:
            pass
    else:
        # try once more, letting exceptions raise
        world.css_find(css_selector)[index].click()
        if not success_condition():
            raise Exception("unsuccessful click")


@world.absorb
def css_check(css_selector, index=0, max_attempts=5, success_condition=lambda: True):
    """
    Checks a check box based on a CSS selector, retrying if it initially fails.

    This function handles errors that may be thrown if the component cannot be clicked on.
    However, there are cases where an error may not be thrown, and yet the operation did not
    actually succeed. For those cases, a success_condition lambda can be supplied to verify that the check worked.

    This function will return True if the check worked (taking into account both errors and the optional
    success_condition).
    """
    assert is_css_present(css_selector), "{} is not present".format(css_selector)
    for _ in range(max_attempts):
        try:
            world.css_find(css_selector)[index].check()
            if success_condition():
                return
        except WebDriverException:
            # Occasionally, MathJax or other JavaScript can cover up
            # an element temporarily.
            # If this happens, wait a second, then try again
            world.wait(1)
        except:
            pass
    else:
        # try once more, letting exceptions raise
        world.css_find(css_selector)[index].check()
        if not success_condition():
            raise Exception("unsuccessful check")


@world.absorb
def css_click_at(css, x_cord=10, y_cord=10):
    '''
    A method to click at x,y coordinates of the element
    rather than in the center of the element
    '''
    element = css_find(css).first
    element.action_chains.move_to_element_with_offset(element._element, x_cord, y_cord)
    element.action_chains.click()
    element.action_chains.perform()


@world.absorb
def id_click(elem_id):
    """
    Perform a click on an element as specified by its id
    """
    world.css_click('#%s' % elem_id)


@world.absorb
def css_fill(css_selector, text, index=0, max_attempts=5):
    assert is_css_present(css_selector)
    return world.retry_on_exception(lambda: world.browser.find_by_css(css_selector)[index].fill(text), max_attempts=max_attempts)


@world.absorb
def click_link(partial_text, index=0, max_attempts=5):
    return world.retry_on_exception(lambda: world.browser.find_link_by_partial_text(partial_text)[index].click(), max_attempts=max_attempts)


@world.absorb
def css_text(css_selector, index=0, max_attempts=5):

    # Wait for the css selector to appear
    if world.is_css_present(css_selector):
        return world.retry_on_exception(lambda: world.browser.find_by_css(css_selector)[index].text, max_attempts=max_attempts)
    else:
        return ""


@world.absorb
def css_value(css_selector, index=0, max_attempts=5):

    # Wait for the css selector to appear
    if world.is_css_present(css_selector):
        return world.retry_on_exception(lambda: world.browser.find_by_css(css_selector)[index].value, max_attempts=max_attempts)
    else:
        return ""


@world.absorb
def css_html(css_selector, index=0, max_attempts=5):
    """
    Returns the HTML of a css_selector and will retry if there is a StaleElementReferenceException
    """
    assert is_css_present(css_selector)
    return world.retry_on_exception(lambda: world.browser.find_by_css(css_selector)[index].html, max_attempts=max_attempts)


@world.absorb
def css_has_class(css_selector, class_name, index=0, max_attempts=5):
    return world.retry_on_exception(lambda: world.css_find(css_selector)[index].has_class(class_name), max_attempts=max_attempts)


@world.absorb
def css_visible(css_selector, index=0, max_attempts=5):
    assert is_css_present(css_selector)
    return world.retry_on_exception(lambda: world.browser.find_by_css(css_selector)[index].visible, max_attempts=max_attempts)


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
def retry_on_exception(func, max_attempts=5):
    attempt = 0
    while attempt < max_attempts:
        try:
            return func()
            break
        except WebDriverException:
            world.wait(1)
            attempt += 1
        except:
            attempt += 1
    assert_true(attempt < max_attempts, 'Ran out of attempts to execute {}'.format(func))

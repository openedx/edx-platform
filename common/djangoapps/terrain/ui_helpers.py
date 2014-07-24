# pylint: disable=C0111
# pylint: disable=W0621

from lettuce import world

import time
import json
import re
import platform

# django_url is assigned late in the process of loading lettuce,
# so we import this as a module, and then read django_url from
# it to get the correct value
import lettuce.django


from textwrap import dedent
from urllib import quote_plus
from selenium.common.exceptions import (
    WebDriverException, TimeoutException,
    StaleElementReferenceException, InvalidElementStateException)
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from nose.tools import assert_true  # pylint: disable=no-name-in-module

GLOBAL_WAIT_FOR_TIMEOUT = 60

REQUIREJS_WAIT = {
    # Settings - Schedule & Details
    re.compile('^Schedule & Details Settings \|'): [
        "jquery", "js/base", "js/models/course",
        "js/models/settings/course_details", "js/views/settings/main"],

    # Settings - Advanced Settings
    re.compile('^Advanced Settings \|'): [
        "jquery", "js/base", "js/models/course", "js/models/settings/advanced",
        "js/views/settings/advanced", "codemirror"],

    # Unit page
    re.compile('^Unit \|'): [
        "jquery", "js/base", "js/models/xblock_info", "js/views/pages/container",
        "js/collections/component_template", "xmodule", "coffee/src/main", "xblock/cms.runtime.v1"],

    # Content - Outline
    # Note that calling your org, course number, or display name, 'course' will mess this up
    re.compile('^Course Outline \|'): [
        "js/base", "js/models/course", "js/models/location", "js/models/section",
        "js/views/section_edit"],

    # Dashboard
    re.compile('^My Courses \|'): [
        "js/sock", "gettext", "js/base",
        "jquery.ui", "coffee/src/main", "underscore"],

    # Upload
    re.compile(r'^\s*Files & Uploads'): [
        'js/base', 'jquery.ui', 'coffee/src/main', 'underscore',
        'js/views/assets', 'js/views/asset'
    ]
}


@world.absorb
def wait(seconds):
    time.sleep(float(seconds))


@world.absorb
def wait_for_js_to_load():
    requirements = None
    for test, req in REQUIREJS_WAIT.items():
        if test.search(world.browser.title):
            requirements = req
            break
    world.wait_for_requirejs(requirements)


# Selenium's `execute_async_script` function pauses Selenium's execution
# until the browser calls a specific Javascript callback; in effect,
# Selenium goes to sleep until the JS callback function wakes it back up again.
# This callback is passed as the last argument to the script. Any arguments
# passed to this callback get returned from the `execute_async_script`
# function, which allows the JS to communicate information back to Python.
# Ref: https://selenium.googlecode.com/svn/trunk/docs/api/dotnet/html/M_OpenQA_Selenium_IJavaScriptExecutor_ExecuteAsyncScript.htm
@world.absorb
def wait_for_js_variable_truthy(variable):
    """
    Using Selenium's `execute_async_script` function, poll the Javascript
    environment until the given variable is defined and truthy. This process
    guards against page reloads, and seamlessly retries on the next page.
    """
    javascript = """
        var callback = arguments[arguments.length - 1];
        var unloadHandler = function() {{
          callback("unload");
        }}
        addEventListener("beforeunload", unloadHandler);
        addEventListener("unload", unloadHandler);
        var intervalID = setInterval(function() {{
          try {{
            if({variable}) {{
              clearInterval(intervalID);
              removeEventListener("beforeunload", unloadHandler);
              removeEventListener("unload", unloadHandler);
              callback(true);
            }}
          }} catch (e) {{}}
        }}, 10);
    """.format(variable=variable)
    for _ in range(5):  # 5 attempts max
        try:
            result = world.browser.driver.execute_async_script(dedent(javascript))
        except WebDriverException as wde:
            if "document unloaded while waiting for result" in wde.msg:
                result = "unload"
            else:
                raise
        if result == "unload":
            # we ran this on the wrong page. Wait a bit, and try again, when the
            # browser has loaded the next page.
            world.wait(1)
            continue
        else:
            return result


@world.absorb
def wait_for_xmodule():
    "Wait until the XModule Javascript has loaded on the page."
    world.wait_for_js_variable_truthy("XModule")
    world.wait_for_js_variable_truthy("XBlock")


@world.absorb
def wait_for_mathjax():
    "Wait until MathJax is loaded and set up on the page."
    world.wait_for_js_variable_truthy("MathJax.isReady")


class RequireJSError(Exception):
    """
    An error related to waiting for require.js. If require.js is unable to load
    a dependency in the `wait_for_requirejs` function, Python will throw
    this exception to make sure that the failure doesn't pass silently.
    """
    pass


@world.absorb
def wait_for_requirejs(dependencies=None):
    """
    If requirejs is loaded on the page, this function will pause
    Selenium until require is finished loading the given dependencies.
    If requirejs is not loaded on the page, this function will return
    immediately.

    :param dependencies: a list of strings that identify resources that
        we should wait for requirejs to load. By default, requirejs will only
        wait for jquery.
    """
    if not dependencies:
        dependencies = ["jquery"]
    # stick jquery at the front
    if dependencies[0] != "jquery":
        dependencies.insert(0, "jquery")

    javascript = """
        var callback = arguments[arguments.length - 1];
        if(window.require) {{
          requirejs.onError = callback;
          var unloadHandler = function() {{
            callback("unload");
          }}
          addEventListener("beforeunload", unloadHandler);
          addEventListener("unload", unloadHandler);
          require({deps}, function($) {{
            setTimeout(function() {{
              removeEventListener("beforeunload", unloadHandler);
              removeEventListener("unload", unloadHandler);
              callback(true);
            }}, 50);
          }});
        }} else {{
          callback(false);
        }}
    """.format(deps=json.dumps(dependencies))
    for _ in range(5):  # 5 attempts max
        try:
            result = world.browser.driver.execute_async_script(dedent(javascript))
        except WebDriverException as wde:
            if "document unloaded while waiting for result" in wde.msg:
                result = "unload"
            else:
                raise
        if result == "unload":
            # we ran this on the wrong page. Wait a bit, and try again, when the
            # browser has loaded the next page.
            world.wait(1)
            continue
        elif result not in (None, True, False):
            # We got a require.js error
            # Sometimes requireJS will throw an error with requireType=require
            # This doesn't seem to cause problems on the page, so we ignore it
            if result['requireType'] == 'require':
                world.wait(1)
                continue

            # Otherwise, fail and report the error
            else:
                msg = "Error loading dependencies: type={0} modules={1}".format(
                    result['requireType'], result['requireModules'])
                err = RequireJSError(msg)
                err.error = result
                raise err
        else:
            return result


@world.absorb
def wait_for_ajax_complete():
    """
    Wait until all jQuery AJAX calls have completed. "Complete" means that
    either the server has sent a response (regardless of whether the response
    indicates success or failure), or that the AJAX call timed out waiting for
    a response. For more information about the `jQuery.active` counter that
    keeps track of this information, go here:
    http://stackoverflow.com/questions/3148225/jquery-active-function#3148506
    """
    javascript = """
        var callback = arguments[arguments.length - 1];
        if(!window.jQuery) {callback(false);}
        var intervalID = setInterval(function() {
          if(jQuery.active == 0) {
            clearInterval(intervalID);
            callback(true);
          }
        }, 100);
    """
    # Sometimes the ajax when it returns will make the browser reload
    # the DOM, and throw a WebDriverException with the message:
    # 'javascript error: document unloaded while waiting for result'
    for _ in range(5):  # 5 attempts max
        try:
            result = world.browser.driver.execute_async_script(dedent(javascript))
        except WebDriverException as wde:
            if "document unloaded while waiting for result" in wde.msg:
                # Wait a bit, and try again, when the browser has reloaded the page.
                world.wait(1)
                continue
            else:
                raise
        return result


@world.absorb
def visit(url):
    world.browser.visit(lettuce.django.django_url(url))
    wait_for_js_to_load()


@world.absorb
def url_equals(url):
    return world.browser.url == lettuce.django.django_url(url)


@world.absorb
def is_css_present(css_selector, wait_time=30):
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
def css_has_text(css_selector, text, index=0, strip=False):
    """
    Return a boolean indicating whether the element with `css_selector`
    has `text`.

    If `strip` is True, strip whitespace at beginning/end of both
    strings before comparing.

    If there are multiple elements matching the css selector,
    use `index` to indicate which one.
    """
    # If we're expecting a non-empty string, give the page
    # a chance to fill in text fields.
    if text:
        wait_for(lambda _: css_text(css_selector, index=index))

    actual_text = css_text(css_selector, index=index)

    if strip:
        actual_text = actual_text.strip()
        text = text.strip()

    return actual_text == text


@world.absorb
def css_contains_text(css_selector, partial_text, index=0):
    """
    Return a boolean indicating whether the element with `css_selector`
    contains `partial_text`.

    If there are multiple elements matching the css selector,
    use `index` to indicate which one.
    """
    # If we're expecting a non-empty string, give the page
    # a chance to fill in text fields.
    if partial_text:
        wait_for(lambda _: css_text(css_selector, index=index))

    actual_text = css_text(css_selector, index=index)

    return partial_text in actual_text


@world.absorb
def css_has_value(css_selector, value, index=0):
    """
    Return a boolean indicating whether the element with
    `css_selector` has the specified `value`.

    If there are multiple elements matching the css selector,
    use `index` to indicate which one.
    """
    # If we're expecting a non-empty string, give the page
    # a chance to fill in values
    if value:
        wait_for(lambda _: css_value(css_selector, index=index))

    return css_value(css_selector, index=index) == value


@world.absorb
def wait_for(func, timeout=5, timeout_msg=None):
    """
    Calls the method provided with the driver as an argument until the
    return value is not False.
    Throws an error if the WebDriverWait timeout clock expires.
    Otherwise this method will return None.
    """
    msg = timeout_msg or "Timed out after {} seconds.".format(timeout)
    try:
        WebDriverWait(
            driver=world.browser.driver,
            timeout=timeout,
            ignored_exceptions=(StaleElementReferenceException)
        ).until(func)
    except TimeoutException:
        raise TimeoutException(msg)


@world.absorb
def wait_for_present(css_selector, timeout=GLOBAL_WAIT_FOR_TIMEOUT):
    """
    Wait for the element to be present in the DOM.
    """
    wait_for(
        func=lambda _: EC.presence_of_element_located((By.CSS_SELECTOR, css_selector,)),
        timeout=timeout,
        timeout_msg="Timed out waiting for {} to be present.".format(css_selector)
    )


@world.absorb
def wait_for_visible(css_selector, index=0, timeout=GLOBAL_WAIT_FOR_TIMEOUT):
    """
    Wait for the element to be visible in the DOM.
    """
    wait_for(
        func=lambda _: css_visible(css_selector, index),
        timeout=timeout,
        timeout_msg="Timed out waiting for {} to be visible.".format(css_selector)
    )


@world.absorb
def wait_for_invisible(css_selector, timeout=GLOBAL_WAIT_FOR_TIMEOUT):
    """
    Wait for the element to be either invisible or not present on the DOM.
    """
    wait_for(
        func=lambda _: EC.invisibility_of_element_located((By.CSS_SELECTOR, css_selector,)),
        timeout=timeout,
        timeout_msg="Timed out waiting for {} to be invisible.".format(css_selector)
    )


@world.absorb
def wait_for_clickable(css_selector, timeout=GLOBAL_WAIT_FOR_TIMEOUT):
    """
    Wait for the element to be present and clickable.
    """
    wait_for(
        func=lambda _: EC.element_to_be_clickable((By.CSS_SELECTOR, css_selector,)),
        timeout=timeout,
        timeout_msg="Timed out waiting for {} to be clickable.".format(css_selector)
    )


@world.absorb
def css_find(css, wait_time=GLOBAL_WAIT_FOR_TIMEOUT):
    """
    Wait for the element(s) as defined by css locator
    to be present.

    This method will return a WebDriverElement.
    """
    wait_for_present(css_selector=css, timeout=wait_time)
    return world.browser.find_by_css(css)


@world.absorb
def css_click(css_selector, index=0, wait_time=GLOBAL_WAIT_FOR_TIMEOUT, dismiss_alert=False):
    """
    Perform a click on a CSS selector, first waiting for the element
    to be present and clickable.

    This method will return True if the click worked.

    If `dismiss_alert` is true, dismiss any alerts that appear.
    """
    wait_for_clickable(css_selector, timeout=wait_time)
    wait_for_visible(css_selector, index=index, timeout=wait_time)
    assert_true(
        css_visible(css_selector, index=index),
        msg="Element {}[{}] is present but not visible".format(css_selector, index)
    )

    retry_on_exception(lambda: css_find(css_selector)[index].click())

    # Dismiss any alerts that occur.
    # We need to do this before calling `wait_for_js_to_load()`
    # to avoid getting an unexpected alert exception
    if dismiss_alert:
        world.browser.get_alert().accept()

    wait_for_js_to_load()
    return True


@world.absorb
def css_check(css_selector, wait_time=GLOBAL_WAIT_FOR_TIMEOUT):
    """
    Checks a check box based on a CSS selector, first waiting for the element
    to be present and clickable. This is just a wrapper for calling "click"
    because that's how selenium interacts with check boxes and radio buttons.

    Then for synchronization purposes, wait for the element to be checked.
    This method will return True if the check worked.
    """
    css_click(css_selector=css_selector, wait_time=wait_time)
    wait_for(lambda _: css_find(css_selector).selected)
    return True


@world.absorb
def select_option(name, value, wait_time=GLOBAL_WAIT_FOR_TIMEOUT):
    '''
    A method to select an option
    Then for synchronization purposes, wait for the option to be selected.
    This method will return True if the selection worked.
    '''
    select_css = "select[name='{}']".format(name)
    option_css = "option[value='{}']".format(value)

    css_selector = "{} {}".format(select_css, option_css)
    css_click(css_selector=css_selector, wait_time=wait_time)
    wait_for(lambda _: css_has_value(select_css, value))
    return True


@world.absorb
def id_click(elem_id):
    """
    Perform a click on an element as specified by its id
    """
    css_click('#{}'.format(elem_id))


@world.absorb
def css_fill(css_selector, text, index=0):
    """
    Set the value of the element to the specified text.
    Note that this will replace the current value completely.
    Then for synchronization purposes, wait for the value on the page.
    """
    wait_for_visible(css_selector, index=index)
    retry_on_exception(lambda: css_find(css_selector)[index].fill(text))
    wait_for(lambda _: css_has_value(css_selector, text, index=index))
    return True


@world.absorb
def click_link(partial_text, index=0):
    retry_on_exception(lambda: world.browser.find_link_by_partial_text(partial_text)[index].click())
    wait_for_js_to_load()


@world.absorb
def click_link_by_text(text, index=0):
    retry_on_exception(lambda: world.browser.find_link_by_text(text)[index].click())


@world.absorb
def css_text(css_selector, index=0, timeout=GLOBAL_WAIT_FOR_TIMEOUT):
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
    world.wait_for_js_to_load()
    course_content_css = 'li.nav-course-courseware'
    css_click(course_content_css)


@world.absorb
def click_course_settings():
    world.wait_for_js_to_load()
    course_settings_css = 'li.nav-course-settings'
    css_click(course_settings_css)


@world.absorb
def click_tools():
    world.wait_for_js_to_load()
    tools_css = 'li.nav-course-tools'
    css_click(tools_css)


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
def retry_on_exception(func, max_attempts=5, ignored_exceptions=(StaleElementReferenceException, InvalidElementStateException)):
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
        except ignored_exceptions:
            world.wait(1)
            attempt += 1

    assert_true(attempt < max_attempts, 'Ran out of attempts to execute {}'.format(func))


@world.absorb
def disable_jquery_animations():
    """
    Disable JQuery animations on the page.  Any state changes
    will occur immediately to the final state.
    """

    # Ensure that jquery is loaded
    world.wait_for_js_to_load()

    # Disable jQuery animations
    world.browser.execute_script("jQuery.fx.off = true;")

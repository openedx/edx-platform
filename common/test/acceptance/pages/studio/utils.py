"""
Utility methods useful for Studio page tests.
"""
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from bok_choy.javascript import js_defined
from bok_choy.promise import EmptyPromise

from common.test.acceptance.pages.common.utils import click_css, wait_for_notification


@js_defined('window.jQuery')
def press_the_notification_button(page, name):
    # Because the notification uses a CSS transition,
    # Selenium will always report it as being visible.
    # This makes it very difficult to successfully click
    # the "Save" button at the UI level.
    # Instead, we use JavaScript to reliably click
    # the button.
    btn_css = 'div#page-notification button.action-%s' % name.lower()
    page.browser.execute_script("$('{}').focus().click()".format(btn_css))
    page.wait_for_ajax()


def add_discussion(page, menu_index=0):
    """
    Add a new instance of the discussion category.

    menu_index specifies which instance of the menus should be used (based on vertical
    placement within the page).
    """
    page.wait_for_component_menu()
    click_css(page, 'button>span.large-discussion-icon', menu_index)


def add_advanced_component(page, menu_index, name):
    """
    Adds an instance of the advanced component with the specified name.

    menu_index specifies which instance of the menus should be used (based on vertical
    placement within the page).
    """
    # Click on the Advanced icon.
    page.wait_for_component_menu()
    click_css(page, 'button>span.large-advanced-icon', menu_index, require_notification=False)

    # This does an animation to hide the first level of buttons
    # and instead show the Advanced buttons that are available.
    # We should be OK though because click_css turns off jQuery animations

    # Make sure that the menu of advanced components is visible before clicking (the HTML is always on the
    # page, but will have display none until the large-advanced-icon is clicked).
    page.wait_for_element_visibility('.new-component-advanced', 'Advanced component menu is visible')

    # Now click on the component to add it.
    component_css = 'button[data-category={}]'.format(name)
    page.wait_for_element_visibility(component_css, 'Advanced component {} is visible'.format(name))

    # Adding some components, e.g. the Discussion component, will make an ajax call
    # but we should be OK because the click_css method is written to handle that.
    click_css(page, component_css, 0)


def add_component(page, item_type, specific_type, is_advanced_problem=False):
    """
    Click one of the "Add New Component" buttons.

    item_type should be "advanced", "html", "problem", or "video"

    specific_type is required for some types and should be something like
    "Blank Common Problem".
    """
    btn = page.q(css='.add-xblock-component .add-xblock-component-button[data-type={}]'.format(item_type))
    multiple_templates = btn.filter(lambda el: 'multiple-templates' in el.get_attribute('class')).present
    btn.click()
    if multiple_templates:
        sub_template_menu_div_selector = '.new-component-{}'.format(item_type)
        page.wait_for_element_visibility(sub_template_menu_div_selector, 'Wait for the templates sub-menu to appear')
        page.wait_for_element_invisibility(
            '.add-xblock-component .new-component',
            'Wait for the add component menu to disappear'
        )

        # "Common Problem Types" are shown by default.
        # For advanced problem types you must first select the "Advanced" tab.
        if is_advanced_problem:
            advanced_tab = page.q(css='.problem-type-tabs a').filter(text='Advanced').first
            advanced_tab.click()

            # Wait for the advanced tab to be active
            css = '.problem-type-tabs li.ui-tabs-active a'
            page.wait_for(
                lambda: len(page.q(css=css).filter(text='Advanced').execute()) > 0,
                'Waiting for the Advanced problem tab to be active'
            )

        all_options = page.q(css='.new-component-{} ul.new-component-template li button span'.format(item_type))
        chosen_option = all_options.filter(text=specific_type).first
        chosen_option.click()
    wait_for_notification(page)
    page.wait_for_ajax()


def add_components(page, item_type, items, is_advanced_problem=False):
    """
    Adds multiple components of a specific type.
    item_type should be "advanced", "html", "problem", or "video"
    items is a list of components of specific type to be added.
    Please note that if you want to create an advanced problem
    then all other items must be of advanced problem type.
    """
    for item in items:
        add_component(page, item_type, item, is_advanced_problem)


def add_html_component(page, menu_index, boilerplate=None):
    """
    Adds an instance of the HTML component with the specified name.

    menu_index specifies which instance of the menus should be used (based on vertical
    placement within the page).
    """
    # Click on the HTML icon.
    page.wait_for_component_menu()
    click_css(page, 'button>span.large-html-icon', menu_index, require_notification=False)

    # Make sure that the menu of HTML components is visible before clicking
    page.wait_for_element_visibility('.new-component-html', 'HTML component menu is visible')

    # Now click on the component to add it.
    component_css = 'button[data-category=html]'
    if boilerplate:
        component_css += '[data-boilerplate={}]'.format(boilerplate)
    else:
        component_css += ':not([data-boilerplate])'

    page.wait_for_element_visibility(component_css, 'HTML component {} is visible'.format(boilerplate))

    # Adding some components will make an ajax call but we should be OK because
    # the click_css method is written to handle that.
    click_css(page, component_css, 0)


@js_defined('window.jQuery')
def type_in_codemirror(page, index, text, find_prefix="$"):
    script = """
    var cm = {find_prefix}('div.CodeMirror:eq({index})').get(0).CodeMirror;
    CodeMirror.signal(cm, "focus", cm);
    cm.setValue(arguments[0]);
    CodeMirror.signal(cm, "blur", cm);""".format(index=index, find_prefix=find_prefix)
    page.browser.execute_script(script, str(text))


@js_defined('window.jQuery')
def get_codemirror_value(page, index=0, find_prefix="$"):
    return page.browser.execute_script(
        """
        return {find_prefix}('div.CodeMirror:eq({index})').get(0).CodeMirror.getValue();
        """.format(index=index, find_prefix=find_prefix)
    )


def set_input_value(page, css, value):
    """
    Sets the text field with the given label (display name) to the specified value.
    """
    input_element = page.q(css=css).results[0]
    # Click in the input to give it the focus
    input_element.click()
    # Select all, then input the value
    input_element.send_keys(Keys.CONTROL + 'a')
    input_element.send_keys(value)
    # Return the input_element for chaining
    return input_element


def set_input_value_and_save(page, css, value):
    """
    Sets the text field with given label (display name) to the specified value, and presses Save.
    """
    set_input_value(page, css, value).send_keys(Keys.ENTER)
    page.wait_for_ajax()


def drag(page, source_index, target_index, placeholder_height=0):
    """
    Gets the drag handle with index source_index (relative to the vertical layout of the page)
    and drags it to the location of the drag handle with target_index.

    This should drag the element with the source_index drag handle BEFORE the
    one with the target_index drag handle.
    """
    draggables = page.q(css='.drag-handle')
    source = draggables[source_index]
    target = draggables[target_index]
    action = ActionChains(page.browser)
    action.click_and_hold(source).move_to_element_with_offset(
        target, 0, placeholder_height
    )
    if placeholder_height == 0:
        action.release(target).perform()
    else:
        action.release().perform()
    wait_for_notification(page)


def verify_ordering(test_class, page, expected_orderings):
    """
    Verifies the expected ordering of xblocks on the page.
    """
    xblocks = page.xblocks
    blocks_checked = set()
    for expected_ordering in expected_orderings:
        for xblock in xblocks:
            parent = expected_ordering.keys()[0]
            if xblock.name == parent:
                blocks_checked.add(parent)
                children = xblock.children
                expected_length = len(expected_ordering.get(parent))
                test_class.assertEqual(
                    expected_length, len(children),
                    "Number of children incorrect for group {0}. Expected {1} but got {2}.".format(parent, expected_length, len(children)))
                for idx, expected in enumerate(expected_ordering.get(parent)):
                    test_class.assertEqual(expected, children[idx].name)
                    blocks_checked.add(expected)
                break
    test_class.assertEqual(len(blocks_checked), len(xblocks))


def click_studio_help(page):
    """Click the Studio help link in the page footer."""
    page.q(css='.cta-show-sock').click()
    EmptyPromise(
        lambda: page.q(css='.support .list-actions a').results[0].text != '',
        'Support section opened'
    ).fulfill()


def studio_help_links(page):
    """Return the list of Studio help links in the page footer."""
    return page.q(css='.support .list-actions a').results

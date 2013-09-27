#pylint: disable=C0111
#pylint: disable=W0621

from lettuce import world, step
from nose.tools import assert_true, assert_in, assert_equal  # pylint: disable=E0611
from common import create_studio_user, add_course_author, log_into_studio


@step(u'I am in Studio editing a new unit$')
def add_unit(step):
    world.clear_courses()
    course = world.CourseFactory.create()
    section = world.ItemFactory.create(parent_location=course.location)
    world.ItemFactory.create(
        parent_location=section.location,
        category='sequential',
        display_name='Subsection One',)
    user = create_studio_user(is_staff=False)
    add_course_author(user, course)
    log_into_studio()
    css_selectors = ['a.course-link', 'div.section-item a.expand-collapse-icon', 'a.new-unit-item']
    for selector in css_selectors:
        world.css_click(selector)


@step(u'I add this type of single step component:$')
def add_a_single_step_component(step):
    for step_hash in step.hashes:
        component = step_hash['Component']
        assert_in(component, ['Discussion', 'Video'])
        css_selector = 'a[data-type="{}"]'.format(component.lower())
        world.css_click(css_selector)


@step(u'I see this type of single step component:$')
def see_a_single_step_component(step):
    for step_hash in step.hashes:
        component = step_hash['Component']
        assert_in(component, ['Discussion', 'Video'])
        component_css = 'section.xmodule_{}Module'.format(component)
        assert_true(world.is_css_present(component_css),
                    "{} couldn't be found".format(component))


@step(u'I add this type of( Advanced)? (HTML|Problem) component:$')
def add_a_multi_step_component(step, is_advanced, category):
    def click_advanced():
        css = 'ul.problem-type-tabs a[href="#tab2"]'
        world.css_click(css)
        my_css = 'ul.problem-type-tabs li.ui-state-active a[href="#tab2"]'
        assert(world.css_find(my_css))

    def find_matching_link():
        """
        Find the link with the specified text. There should be one and only one.
        """
        # The tab shows links for the given category
        links = world.css_find('div.new-component-{} a'.format(category))

        # Find the link whose text matches what you're looking for
        matched_links = [link for link in links if link.text == step_hash['Component']]

        # There should be one and only one
        assert_equal(len(matched_links), 1)
        return matched_links[0]

    def click_link():
        link.click()

    category = category.lower()
    for step_hash in step.hashes:
        css_selector = 'a[data-type="{}"]'.format(category)
        world.css_click(css_selector)
        world.wait_for_invisible(css_selector)

        if is_advanced:
            # Sometimes this click does not work if you go too fast.
            world.retry_on_exception(click_advanced, max_attempts=5, ignored_exceptions=AssertionError)

        # Retry this in case the list is empty because you tried too fast.
        link = world.retry_on_exception(func=find_matching_link, ignored_exceptions=AssertionError)

        # Wait for the link to be clickable. If you go too fast it is not.
        world.retry_on_exception(click_link)


@step(u'I see (HTML|Problem) components in this order:')
def see_a_multi_step_component(step, category):
    components = world.css_find('li.component section.xmodule_display')
    for idx, step_hash in enumerate(step.hashes):
        if category == 'HTML':
            html_matcher = {
                'Text':
                    '\n    \n',
                'Announcement':
                    '<p> Words of encouragement! This is a short note that most students will read. </p>',
                'E-text Written in LaTeX':
                    '<h2>Example: E-text page</h2>',
            }
            assert_in(html_matcher[step_hash['Component']], components[idx].html)
        else:
            assert_in(step_hash['Component'].upper(), components[idx].text)


@step(u'I add a "([^"]*)" "([^"]*)" component$')
def add_component_catetory(step, component, category):
    assert category in ('single step', 'HTML', 'Problem', 'Advanced Problem')
    given_string = 'I add this type of {} component:'.format(category)
    step.given('{}\n{}\n{}'.format(given_string, '|Component|', '|{}|'.format(component)))


@step(u'I delete all components$')
def delete_all_components(step):
    delete_btn_css = 'a.delete-button'
    prompt_css = 'div#prompt-warning'
    btn_css = '{} a.button.action-primary'.format(prompt_css)
    saving_mini_css = 'div#page-notification .wrapper-notification-mini'
    count = len(world.css_find('ol.components li.component'))
    for _ in range(int(count)):
        world.css_click(delete_btn_css)
        assert_true(world.is_css_present('{}.is-shown'.format(prompt_css)),
            msg='Waiting for the confirmation prompt to be shown')

        # Pressing the button via css was not working reliably for the last component
        # when run in Chrome.
        if world.browser.driver_name is 'Chrome':
            world.browser.execute_script("$('{}').click()".format(btn_css))
        else:
            world.css_click(btn_css)

        # Wait for the saving notification to pop up then disappear
        if world.is_css_present('{}.is-shown'.format(saving_mini_css)):
            world.css_find('{}.is-hiding'.format(saving_mini_css))


@step(u'I see no components')
def see_no_components(steps):
    assert world.is_css_not_present('li.component')


@step(u'I delete a component')
def delete_one_component(step):
    world.css_click('a.delete-button')


@step(u'I edit and save a component')
def edit_and_save_component(step):
    world.css_click('.edit-button')
    world.css_click('.save-button')

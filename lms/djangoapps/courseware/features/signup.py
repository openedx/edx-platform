#pylint: disable=C0111
#pylint: disable=W0621

from lettuce import world, step


@step('I fill in "([^"]*)" on the registration form with "([^"]*)"$')
def when_i_fill_in_field_on_the_registration_form_with_value(step, field, value):
    def fill_in_registration():
        register_form = world.browser.find_by_css('form#register-form')
        form_field = register_form.find_by_name(field)
        form_field.fill(value)
    world.retry_on_exception(fill_in_registration)


@step('I submit the registration form$')
def i_press_the_button_on_the_registration_form(step):
    def submit_registration():
        register_form = world.browser.find_by_css('form#register-form')
        register_form.find_by_name('submit').click()
    world.retry_on_exception(submit_registration)


@step('I check the checkbox named "([^"]*)"$')
def i_check_checkbox(step, checkbox):
    css_selector = 'input[name={}]'.format(checkbox)
    world.css_check(css_selector)


@step('I should see "([^"]*)" in the dashboard banner$')
def i_should_see_text_in_the_dashboard_banner_section(step, text):
    css_selector = "section.dashboard-banner h2"
    assert (text in world.css_text(css_selector))

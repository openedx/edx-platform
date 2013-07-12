#pylint: disable=C0111
#pylint: disable=W0621

from lettuce import world, step


@step('I fill in the registration form$')
def i_fill_in_the_registration_form(step):
    def fill_in_reg_form():
        register_form = world.css_find('form#register_form')
        register_form.find_by_name('email').fill('robot+studio@edx.org')
        register_form.find_by_name('password').fill('test')
        register_form.find_by_name('username').fill('robot-studio')
        register_form.find_by_name('name').fill('Robot Studio')
        register_form.find_by_name('terms_of_service').check()
    world.retry_on_exception(fill_in_reg_form)


@step('I press the Create My Account button on the registration form$')
def i_press_the_button_on_the_registration_form(step):
    submit_css = 'form#register_form button#submit'
    world.css_click(submit_css)


@step('I should see be on the studio home page$')
def i_should_see_be_on_the_studio_home_page(step):
    step.given('I should see the message "My Courses"')


@step(u'I should see the message "([^"]*)"$')
def i_should_see_the_message(step, msg):
    assert world.browser.is_text_present(msg, 5)

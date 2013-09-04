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
        register_form.find_by_name('terms_of_service').click()
    world.retry_on_exception(fill_in_reg_form)


@step('I press the Create My Account button on the registration form$')
def i_press_the_button_on_the_registration_form(step):
    submit_css = 'form#register_form button#submit'
    world.css_click(submit_css)


@step('I should see an email verification prompt')
def i_should_see_an_email_verification_prompt(step):
    world.css_has_text('h1.page-header', u'My Courses')
    world.css_has_text('div.msg h3.title', u'We need to verify your email address')


@step(u'I fill in and submit the signin form$')
def i_fill_in_the_signin_form(step):
    def fill_login_form():
        login_form = world.browser.find_by_css('form#login_form')
        login_form.find_by_name('email').fill('robot+studio@edx.org')
        login_form.find_by_name('password').fill('test')
        login_form.find_by_name('submit').click()
    world.retry_on_exception(fill_login_form)

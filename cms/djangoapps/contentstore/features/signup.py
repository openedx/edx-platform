# pylint: disable=missing-docstring
# pylint: disable=no-member

from lettuce import step, world


@step('I fill in the registration form$')
def i_fill_in_the_registration_form(_step):
    def fill_in_reg_form():
        register_form = world.css_find('form#register_form')
        register_form.find_by_name('email').fill('robot+studio@edx.org')
        register_form.find_by_name('password').fill('test')
        register_form.find_by_name('username').fill('robot-studio')
        register_form.find_by_name('name').fill('Robot Studio')
        register_form.find_by_name('terms_of_service').click()
    world.retry_on_exception(fill_in_reg_form)


@step('I press the Create My Account button on the registration form$')
def i_press_the_button_on_the_registration_form(_step):
    submit_css = 'form#register_form button#submit'
    world.css_click(submit_css)


@step('I should see an email verification prompt')
def i_should_see_an_email_verification_prompt(_step):
    world.css_has_text('h1.page-header', u'Studio Home')
    world.css_has_text('div.msg h3.title', u'We need to verify your email address')


@step(u'I fill in and submit the signin form$')
def i_fill_in_the_signin_form(_step):
    def fill_login_form():
        login_form = world.browser.find_by_css('form#login_form')
        login_form.find_by_name('email').fill('robot+studio@edx.org')
        login_form.find_by_name('password').fill('test')
        login_form.find_by_name('submit').click()
    world.retry_on_exception(fill_login_form)


@step(u'I should( not)? see a login error message$')
def i_should_see_a_login_error(_step, should_not_see):
    if should_not_see:
        # the login error may be absent or invisible. Check absence first,
        # because css_visible will throw an exception if the element is not present
        if world.is_css_present('div#login_error'):
            assert not world.css_visible('div#login_error')
    else:
        assert world.css_visible('div#login_error')


@step(u'I fill in and submit the signin form incorrectly$')
def i_goof_in_the_signin_form(_step):
    def fill_login_form():
        login_form = world.browser.find_by_css('form#login_form')
        login_form.find_by_name('email').fill('robot+studio@edx.org')
        login_form.find_by_name('password').fill('oops')
        login_form.find_by_name('submit').click()
    world.retry_on_exception(fill_login_form)


@step(u'I edit the password field$')
def i_edit_the_password_field(_step):
    password_css = 'form#login_form input#password'
    world.css_fill(password_css, 'test')


@step(u'I submit the signin form$')
def i_submit_the_signin_form(_step):
    submit_css = 'form#login_form button#submit'
    world.css_click(submit_css)

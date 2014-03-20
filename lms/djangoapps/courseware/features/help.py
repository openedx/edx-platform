# pylint: disable=C0111
# pylint: disable=W0621

from lettuce import world, step


@step(u'I open the help form')
def open_help_modal(step):
    help_css = 'div.help-tab'
    world.css_click(help_css)


@step(u'I report a "([^"]*)"$')
def submit_problem_type(step, submission_type):
    type_css = '#feedback_link_{}'.format(submission_type)
    world.css_click(type_css)
    fill_field('name', 'Robot')
    fill_field('email', 'robot@edx.org')
    fill_field('subject', 'Test Issue')
    fill_field('details', 'I am having a problem')
    submit_css = 'div.submit'
    world.css_click(submit_css)


@step(u'I report a "([^"]*)" without saying who I am$')
def submit_partial_problem_type(step, submission_type):
    type_css = '#feedback_link_{}'.format(submission_type)
    world.css_click(type_css)
    fill_field('subject', 'Test Issue')
    fill_field('details', 'I am having a problem')
    submit_css = 'div.submit'
    world.css_click(submit_css)


@step(u'I should see confirmation that the issue was received')
def see_confirmation(step):
    assert world.browser.evaluate_script("$('input[value=\"Submit\"]').attr('disabled')") == 'disabled'


def fill_field(name, info):
    def fill_info():
        form_css = 'form.feedback_form'
        form = world.css_find(form_css)
        form.find_by_name(name).fill(info)
    world.retry_on_exception(fill_info)

#pylint: disable=C0111
#pylint: disable=W0621

from lettuce import world, step

@step(u'I click the help modal')
def open_help_modal(step):
	help_css = 'div.help-tab'
	world.css_click(help_css)


@step(u'I report a "([^"]*)"$')
def select_problem_type(step, submission_type):
	type_css = '#feedback_link_{}'.format(submission_type)
	world.css_click(type_css)


@step(u'I fill "([^"]*)" with "([^"]*)"$')
def fill_field(step, name, info):
	form_css = 'form.feedback_form'
	form = world.css_find(form_css)
	form.find_by_name(name).fill(info)


@step(u'I submit the issue')
def submit_issue(step):
	submit_css = 'div.submit'
	world.css_click(submit_css)


@step(u'The submit button should be disabled')
def see_confirmation(step):
	assert world.browser.evaluate_script("$('input[value=\"Submit\"]').attr('disabled')") == 'disabled'

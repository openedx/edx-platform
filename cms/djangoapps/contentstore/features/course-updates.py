# pylint: disable=missing-docstring

from cms.djangoapps.contentstore.features.common import type_in_codemirror, get_codemirror_value
from lettuce import world, step
from nose.tools import assert_in


@step(u'I go to the course updates page')
def go_to_updates(_step):
    menu_css = 'li.nav-course-courseware'
    updates_css = 'li.nav-course-courseware-updates a'
    world.css_click(menu_css)
    world.css_click(updates_css)
    world.wait_for_visible('#course-handouts-view')


@step(u'I change the handout from "([^"]*)" to "([^"]*)"$')
def change_existing_handout(_step, before, after):
    verify_text_in_editor_and_update('div.course-handouts .edit-button', before, after)


@step(u'I modify the handout to "([^"]*)"$')
def edit_handouts(_step, text):
    edit_css = 'div.course-handouts > .edit-button'
    world.css_click(edit_css)
    change_text(text)


@step(u'I see the handout "([^"]*)"$')
def check_handout(_step, handout):
    handout_css = 'div.handouts-content'
    assert_in(handout, world.css_html(handout_css))


@step(u'I see the handout image link "([^"]*)"$')
def check_handout_image_link(_step, image_file):
    handout_css = 'div.handouts-content'
    handout_html = world.css_html(handout_css)
    asset_key = world.scenario_dict['COURSE'].id.make_asset_key(asset_type='asset', path=image_file)
    assert_in(unicode(asset_key), handout_html)


@step(u'I see the handout error text')
def check_handout_error(_step):
    handout_error_css = 'div#handout_error'
    assert world.css_has_class(handout_error_css, 'is-shown')


@step(u'I see handout save button disabled')
def check_handout_error(_step):
    handout_save_button = 'form.edit-handouts-form .save-button'
    assert world.css_has_class(handout_save_button, 'is-disabled')


@step(u'I edit the handout to "([^"]*)"$')
def edit_handouts(_step, text):
    type_in_codemirror(0, text)


@step(u'I see handout save button re-enabled')
def check_handout_error(_step):
    handout_save_button = 'form.edit-handouts-form .save-button'
    assert not world.css_has_class(handout_save_button, 'is-disabled')


@step(u'I save handout edit')
def check_handout_error(_step):
    save_css = '.save-button'
    world.css_click(save_css)


def change_text(text):
    type_in_codemirror(0, text)
    save_css = '.save-button'
    world.css_click(save_css)


def verify_text_in_editor_and_update(button_css, before, after):
    world.css_click(button_css)
    text = get_codemirror_value()
    assert_in(before, text)
    change_text(after)


@step('I see a "(saving|deleting)" notification')
def i_see_a_mini_notification(_step, _type):
    saving_css = '.wrapper-notification-mini'
    assert world.is_css_present(saving_css)

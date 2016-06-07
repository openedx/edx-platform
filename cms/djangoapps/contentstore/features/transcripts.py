# disable missing docstring
# pylint: disable=missing-docstring

import os
from lettuce import world, step

from django.conf import settings

from xmodule.contentstore.content import StaticContent
from xmodule.contentstore.django import contentstore
from xmodule.exceptions import NotFoundError
from splinter.request_handler.request_handler import RequestHandler

TEST_ROOT = settings.COMMON_TEST_DATA_ROOT

# We should wait 300 ms for event handler invocation + 200ms for safety.
DELAY = 0.5

ERROR_MESSAGES = {
    'url_format': u'Incorrect url format.',
    'file_type': u'Link types should be unique.',
    'links_duplication': u'Links should be unique.',
}

STATUSES = {
    'found': u'Timed Transcript Found',
    'not found on edx': u'No EdX Timed Transcript',
    'not found': u'No Timed Transcript',
    'replace': u'Timed Transcript Conflict',
    'uploaded_successfully': u'Timed Transcript Uploaded Successfully',
    'use existing': u'Confirm Timed Transcript',
}

SELECTORS = {
    'error_bar': '.transcripts-error-message',
    'url_inputs': '.videolist-settings-item input.input',
    'collapse_link': '.collapse-action.collapse-setting',
    'collapse_bar': '.videolist-extra-videos',
    'status_bar': '.transcripts-message-status',
}

# button type , button css selector, button message
TRANSCRIPTS_BUTTONS = {
    'import': ('.setting-import', 'Import YouTube Transcript'),
    'download_to_edit': ('.setting-download', 'Download Transcript for Editing'),
    'disabled_download_to_edit': ('.setting-download.is-disabled', 'Download Transcript for Editing'),
    'upload_new_timed_transcripts': ('.setting-upload', 'Upload New Transcript'),
    'replace': ('.setting-replace', 'Yes, replace the edX transcript with the YouTube transcript'),
    'choose': ('.setting-choose', 'Timed Transcript from {}'),
    'use_existing': ('.setting-use-existing', 'Use Current Transcript'),
}


@step('I clear fields$')
def clear_fields(_step):

    # Clear the input fields and trigger an 'input' event
    script = """
        $('{selector}')
            .prop('disabled', false)
            .removeClass('is-disabled')
            .attr('aria-disabled', false)
            .val('')
            .trigger('input');
    """.format(selector=SELECTORS['url_inputs'])
    world.browser.execute_script(script)

    world.wait(DELAY)
    world.wait_for_ajax_complete()


@step('I clear field number (.+)$')
def clear_field(_step, index):
    index = int(index) - 1
    world.css_fill(SELECTORS['url_inputs'], '', index)

    # For some reason ChromeDriver doesn't trigger an 'input' event after filling
    # the field with an empty value. That's why we trigger it manually via jQuery.
    world.trigger_event(SELECTORS['url_inputs'], event='input', index=index)

    world.wait(DELAY)
    world.wait_for_ajax_complete()


@step('I expect (.+) inputs are disabled$')
def inputs_are_disabled(_step, indexes):
    index_list = [int(i.strip()) - 1 for i in indexes.split(',')]
    for index in index_list:
        el = world.css_find(SELECTORS['url_inputs'])[index]

        assert el['disabled']


@step('I expect inputs are enabled$')
def inputs_are_enabled(_step):
    for index in range(3):
        el = world.css_find(SELECTORS['url_inputs'])[index]

        assert not el['disabled']


@step('I do not see error message$')
def i_do_not_see_error_message(_step):
    assert not world.css_visible(SELECTORS['error_bar'])


@step('I see error message "([^"]*)"$')
def i_see_error_message(_step, error):
    assert world.css_has_text(SELECTORS['error_bar'], ERROR_MESSAGES[error])


@step('I do not see status message$')
def i_do_not_see_status_message(_step):
    assert not world.css_visible(SELECTORS['status_bar'])


@step('I see status message "([^"]*)"$')
def i_see_status_message(_step, status):
    assert not world.css_visible(SELECTORS['error_bar'])
    assert world.css_has_text(SELECTORS['status_bar'], STATUSES[status])

    DOWNLOAD_BUTTON = TRANSCRIPTS_BUTTONS["download_to_edit"][0]
    if world.is_css_present(DOWNLOAD_BUTTON, wait_time=1) and not world.css_find(DOWNLOAD_BUTTON)[0].has_class('is-disabled'):
        assert _transcripts_are_downloaded()


@step('I (.*)see button "([^"]*)"$')
def i_see_button(_step, not_see, button_type):
    button = button_type.strip()

    if not_see.strip():
        assert world.is_css_not_present(TRANSCRIPTS_BUTTONS[button][0])
    else:
        assert world.css_has_text(TRANSCRIPTS_BUTTONS[button][0], TRANSCRIPTS_BUTTONS[button][1])


@step('I (.*)see (.*)button "([^"]*)" number (\d+)$')
def i_see_button_with_custom_text(_step, not_see, button_type, custom_text, index):
    button = button_type.strip()
    custom_text = custom_text.strip()
    index = int(index.strip()) - 1

    if not_see.strip():
        assert world.is_css_not_present(TRANSCRIPTS_BUTTONS[button][0])
    else:
        assert world.css_has_text(TRANSCRIPTS_BUTTONS[button][0], TRANSCRIPTS_BUTTONS[button][1].format(custom_text), index)


@step('I click transcript button "([^"]*)"$')
def click_button_transcripts_variant(_step, button_type):
    button = button_type.strip()
    world.css_click(TRANSCRIPTS_BUTTONS[button][0])
    world.wait_for_ajax_complete()


@step('I click transcript button "([^"]*)" number (\d+)$')
def click_button_index(_step, button_type, index):
    button = button_type.strip()
    index = int(index.strip()) - 1

    world.css_click(TRANSCRIPTS_BUTTONS[button][0], index)
    world.wait_for_ajax_complete()


@step('I remove "([^"]+)" transcripts id from store')
def remove_transcripts_from_store(_step, subs_id):
    """Remove from store, if transcripts content exists."""
    filename = 'subs_{0}.srt.sjson'.format(subs_id.strip())
    content_location = StaticContent.compute_location(
        world.scenario_dict['COURSE'].id,
        filename
    )
    try:
        content = contentstore().find(content_location)
        contentstore().delete(content.location)
        print 'Transcript file was removed from store.'
    except NotFoundError:
        print 'Transcript file was NOT found and not removed.'


@step('I enter a "([^"]+)" source to field number (\d+)$')
def i_enter_a_source(_step, link, index):
    index = int(index) - 1

    if index is not 0 and not world.css_visible(SELECTORS['collapse_bar']):
        world.css_click(SELECTORS['collapse_link'])

        assert world.css_visible(SELECTORS['collapse_bar'])

    world.css_fill(SELECTORS['url_inputs'], link, index)
    world.wait(DELAY)
    world.wait_for_ajax_complete()


@step('I upload the transcripts file "([^"]*)"$')
def upload_file(_step, file_name):
    path = os.path.join(TEST_ROOT, 'uploads/', file_name.strip())
    world.browser.execute_script("$('form.file-chooser').show()")
    world.browser.attach_file('transcript-file', os.path.abspath(path))
    world.wait_for_ajax_complete()


@step('I see "([^"]*)" text in the captions')
def check_text_in_the_captions(_step, text):
    world.wait_for_present('.video.is-captions-rendered')
    world.wait_for(lambda _: world.css_text('.subtitles'), timeout=30)
    actual_text = world.css_text('.subtitles')
    assert text in actual_text


@step('I see value "([^"]*)" in the field "([^"]*)"$')
def check_transcripts_field(_step, values, field_name):
    world.select_editor_tab('Advanced')
    tab = world.css_find('#settings-tab').first
    field_id = '#' + tab.find_by_xpath('.//label[text()="%s"]' % field_name.strip())[0]['for']
    values_list = [i.strip() == world.css_value(field_id) for i in values.split('|')]
    assert any(values_list)
    world.select_editor_tab('Basic')


@step('I save changes$')
def save_changes(_step):
    world.save_component()


@step('I open tab "([^"]*)"$')
def open_tab(_step, tab_name):
    world.select_editor_tab(tab_name)


@step('I set value "([^"]*)" to the field "([^"]*)"$')
def set_value_transcripts_field(_step, value, field_name):
    tab = world.css_find('#settings-tab').first
    XPATH = './/label[text()="{name}"]'.format(name=field_name)
    SELECTOR = '#' + tab.find_by_xpath(XPATH)[0]['for']
    element = world.css_find(SELECTOR).first
    if element['type'] == 'text':
        SCRIPT = '$("{selector}").val("{value}").change()'.format(
            selector=SELECTOR,
            value=value
        )
        world.browser.execute_script(SCRIPT)
        assert world.css_has_value(SELECTOR, value)
    else:
        assert False, 'Incorrect element type.'
    world.wait_for_ajax_complete()


@step('I revert the transcript field "([^"]*)"$')
def revert_transcripts_field(_step, field_name):
    world.revert_setting_entry(field_name)


def _transcripts_are_downloaded():
    world.wait_for_ajax_complete()
    request = RequestHandler()
    DOWNLOAD_BUTTON = world.css_find(TRANSCRIPTS_BUTTONS["download_to_edit"][0]).first
    url = DOWNLOAD_BUTTON['href']
    request.connect(url)

    return request.status_code.is_success()

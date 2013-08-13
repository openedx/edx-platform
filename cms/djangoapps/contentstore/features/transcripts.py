# disable missing docstring
# pylint: disable=C0111

from lettuce import world, step
from django.conf import settings
import os


TEST_ROOT = settings.COMMON_TEST_DATA_ROOT

DELAY = 1

ERROR_MESSAGES = {
    'url_format': u'Incorrect url format.',
    'file_type': u'Link types should be unique.',
}

STATUSES = {
    'found': u'Timed Transcripts Found',
    'not found': u'No Timed Transcripts',
    'replace': u'Timed Transcripts Conflict',
    'uploaded_successfully': u'Timed Transcripts uploaded successfully',
    'use existing': u'Timed Transcripts Not Updated',
}

SELECTORS = {
    'error_bar': '.transcripts-error-message',
    'url_inputs': '.videolist-settings-item input.input',
    'collapse_link': '.collapse-action.collapse-setting',
    'collapse_bar': '.videolist-extra-videos',
    'status_bar': '.transcripts-message-status',
}

# button type , button css selector, button message
BUTTONS = {
    'import': ('.setting-import',  'Import from YouTube'),
    'download_to_edit': ('.setting-download', 'Download to Edit'),
    'disabled_download_to_edit': ('.setting-download.is-disabled', 'Download to Edit'),
    'upload_new_timed_transcripts': ('.setting-upload',  'Upload New Timed Transcripts'),
    'replace': ('.setting-replace', 'Yes, Replace EdX Timed Transcripts with YouTube Timed Transcripts'),
    'choose': ('.setting-choose', 'Timed Transcripts from {}'),
    'use_existing': ('.setting-use-existing', 'Use Existing Timed Transcripts'),
}


@step('I clear fields$')
def clear_fields(_step):
    world.css_click('.metadata-videolist-enum .setting-clear')


@step('I clear field number (.+)$')
def clear_field(_step, index):
    index = int(index) - 1
    world.css_fill(SELECTORS['url_inputs'], '', index)
    # In some reason chromeDriver doesn't trigger 'input' event after filling
    # field by an empty value. That's why we trigger it manually via jQuery.
    world.browser.execute_script("$('{0}').eq({1}).trigger('input')".format(SELECTORS['url_inputs'], index))


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


@step('I (.*)see (.*)error message$')
def i_see_error_message(_step, not_error, error):
    world.wait(DELAY)
    if not_error:
        assert not world.css_visible(SELECTORS['error_bar'])
    else:
        assert world.css_has_text(SELECTORS['error_bar'], ERROR_MESSAGES[error.strip()])


@step('I (.*)see (.*)status message$')
def i_see_status_message(_step, not_see, status):
    world.wait(DELAY)
    if not_see:
        assert not world.css_visible(SELECTORS['status_bar'])
    else:
        assert world.css_has_text(SELECTORS['status_bar'], STATUSES[status.strip()])


@step('I (.*)see (.*)button$')
def i_see_button(_step, not_see, button_type):
    world.wait(DELAY)
    button = button_type.strip()
    if BUTTONS.get(button):
        if not_see:
            assert world.is_css_not_present(BUTTONS[button][0])
        else:
            assert world.css_has_text(BUTTONS[button][0], BUTTONS[button][1])
    else:
        assert False  # not implemented


@step('I (.*)see (.*)button (.*) number (\d+)$')
def i_see_button_with_custom_text(_step, not_see, button_type, custom_text, index):
    world.wait(DELAY)
    button = button_type.strip()
    custom_text = custom_text.strip()
    index = int(index.strip()) - 1
    if BUTTONS.get(button):
        if not_see:
            assert world.is_css_not_present(BUTTONS[button][0])
        else:
            assert world.css_has_text(BUTTONS[button][0], BUTTONS[button][1].format(custom_text), index)
    else:
        assert False  # not implemented


@step('I click (.*)button$')
def click_button(_step, button_type):
    world.wait(DELAY)
    button = button_type.strip()
    if BUTTONS.get(button):
        world.css_click(BUTTONS[button][0])
    else:
        assert False  # not implemented


@step('I click (.*)button number (\d+)$')
def click_button_index(_step, button_type, index):
    world.wait(DELAY)
    button = button_type.strip()
    index = int(index.strip()) - 1
    if BUTTONS.get(button):
        world.css_click(BUTTONS[button][0], index)
    else:
        assert False  # not implemented


@step('I run ipdb')
def run_ipdb(_step):
    """Run ipdb as step for easy debugging"""
    import ipdb
    ipdb.set_trace()
    assert True


@step('I remove (.*)transcripts id from store')
def remove_transcripts_from_store(_step, subs_id):
    """Remove from store, if transcripts content exists."""
    from xmodule.contentstore.content import StaticContent
    from xmodule.contentstore.django import contentstore
    from xmodule.exceptions import NotFoundError
    filename = 'subs_{0}.srt.sjson'.format(subs_id.strip())
    content_location = StaticContent.compute_location(
        world.scenario_dict['COURSE'].org,
        world.scenario_dict['COURSE'].number,
        filename
    )
    try:
        content = contentstore().find(content_location)
        contentstore().delete(content.get_id())
        print('Transcript file was removed from store.')
    except NotFoundError:
        print('Transcript file was NOT found and not removed.')


@step('I enter a (.+) source to field number (\d+)$')
def i_enter_a_source(_step, link, index):
    index = int(index) - 1
    world.wait(DELAY)

    if index is not 0 and not world.css_visible(SELECTORS['collapse_bar']):
        world.css_click(SELECTORS['collapse_link'])
        assert world.css_visible(SELECTORS['collapse_bar'])

    world.css_fill(SELECTORS['url_inputs'], link, index)


@step('I upload the transcripts file "([^"]*)"$')
def upload_file(_step, file_name):
    path = os.path.join(TEST_ROOT, 'uploads/', file_name.strip())
    world.browser.execute_script("$('form.file-chooser').show()")
    world.browser.attach_file('file', os.path.abspath(path))
    world.wait(DELAY)


@step('I see "([^"]*)" value in the "([^"]*)" field$')
def check_transcripts_field(_step, values, field_name):
    world.wait(DELAY)
    world.click_link_by_text('Advanced')
    field_id = '#' + world.browser.find_by_xpath('//label[text()="%s"]' % field_name.strip())[0]['for']
    values_list = [i.strip() == world.css_value(field_id) for i in values.split('|')]
    assert any(values_list)
    world.click_link_by_text('Basic')


@step('I save changes$')
def save_changes(_step):
    save_css = 'a.save-button'
    world.css_click(save_css)


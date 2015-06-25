# -*- coding: utf-8 -*-
# disable missing docstring
# pylint: disable=missing-docstring

import requests
from lettuce import world, step
from nose.tools import assert_true, assert_equal, assert_in, assert_not_equal  # pylint: disable=no-name-in-module
from terrain.steps import reload_the_page
from django.conf import settings
from common import upload_file, attach_file

TEST_ROOT = settings.COMMON_TEST_DATA_ROOT

DISPLAY_NAME = "Component Display Name"
NATIVE_LANGUAGES = {lang: label for lang, label in settings.LANGUAGES if len(lang) == 2}
LANGUAGES = {
    lang: NATIVE_LANGUAGES.get(lang, display)
    for lang, display in settings.ALL_LANGUAGES
}

LANGUAGES.update({
    'table': 'Table of Contents'
})

TRANSLATION_BUTTONS = {
    'add': '.metadata-video-translations .create-action',
    'upload': '.metadata-video-translations .upload-action',
    'download': '.metadata-video-translations .download-action',
    'remove': '.metadata-video-translations .remove-action',
    'clear': '.metadata-video-translations .setting-clear',
}

VIDEO_MENUS = {
    'language': '.lang .menu',
}


class RequestHandlerWithSessionId(object):
    def get(self, url):
        """
        Sends a request.
        """
        kwargs = dict()

        session_id = [{i['name']:i['value']} for i in world.browser.cookies.all() if i['name'] == u'sessionid']
        if session_id:
            kwargs.update({
                'cookies': session_id[0]
            })

        response = requests.get(url, **kwargs)
        self.response = response
        self.status_code = response.status_code
        self.headers = response.headers
        self.content = response.content

        return self

    def is_success(self):
        """
        Returns `True` if the response was succeed, otherwise, returns `False`.
        """
        if self.status_code < 400:
            return True
        return False

    def check_header(self, name, value):
        """
        Returns `True` if the response header exist and has appropriate value,
        otherwise, returns `False`.
        """
        if value in self.headers.get(name, ''):
            return True
        return False


def success_upload_file(filename):
    upload_file(filename, sub_path="uploads/")
    world.css_has_text('#upload_confirm', 'Success!')
    world.is_css_not_present('.wrapper-modal-window-assetupload', wait_time=30)


def get_translations_container():
    return world.browser.find_by_xpath('//label[text()="Transcript Languages"]/following-sibling::div')


def get_setting_container(lang_code):
    try:
        get_xpath = lambda value: './/descendant::a[@data-lang="{}" and contains(@class,"remove-setting")]/parent::*'.format(value)
        return get_translations_container().find_by_xpath(get_xpath(lang_code)).first
    except Exception:
        return None


def get_last_dropdown():
    return get_translations_container().find_by_xpath('.//descendant::select[last()]').last


def choose_option(dropdown, value):
    dropdown.find_by_value(value)[0].click()


def choose_new_lang(lang_code):
    world.css_click(TRANSLATION_BUTTONS['add'])
    choose_option(get_last_dropdown(), lang_code)
    assert_equal(get_last_dropdown().value, lang_code, "Option with provided value is not available or was not selected")


def open_menu(menu):
    world.browser.execute_script("$('{selector}').parent().addClass('is-opened')".format(
        selector=VIDEO_MENUS[menu]
    ))


@step('I have set "transcript display" to (.*)$')
def set_show_captions(step, setting):
    # Prevent cookies from overriding course settings
    world.browser.cookies.delete('hide_captions')

    world.edit_component()
    world.select_editor_tab('Advanced')
    world.browser.select('Show Transcript', setting)
    world.save_component()


@step('when I view the video it (.*) show the captions$')
def shows_captions(_step, show_captions):
    world.wait_for_js_variable_truthy("Video")
    world.wait(0.5)
    if show_captions == 'does not':
        assert_true(world.is_css_present('div.video.closed'))
    else:
        assert_true(world.is_css_not_present('div.video.closed'))

    # Prevent cookies from overriding course settings
    world.browser.cookies.delete('hide_captions')
    world.browser.cookies.delete('current_player_mode')


@step('I see the correct video settings and default values$')
def correct_video_settings(_step):
    expected_entries = [
        # basic
        [DISPLAY_NAME, 'Video', False],
        ['Default Video URL', 'http://youtu.be/3_yD_cEKoCk, , ', False],

        # advanced
        [DISPLAY_NAME, 'Video', False],
        ['Default Timed Transcript', '', False],
        ['Download Transcript Allowed', 'False', False],
        ['Downloadable Transcript URL', '', False],
        ['Show Transcript', 'True', False],
        ['Transcript Languages', '', False],
        ['Upload Handout', '', False],
        ['Video Available on Web Only', 'False', False],
        ['Video Download Allowed', 'False', False],
        ['Video File URLs', '', False],
        ['Video Start Time', '00:00:00', False],
        ['Video Stop Time', '00:00:00', False],
        ['YouTube ID', '3_yD_cEKoCk', False],
        ['YouTube ID for .75x speed', '', False],
        ['YouTube ID for 1.25x speed', '', False],
        ['YouTube ID for 1.5x speed', '', False]
    ]
    world.verify_all_setting_entries(expected_entries)


@step('my video display name change is persisted on save$')
def video_name_persisted(step):
    world.save_component()
    reload_the_page(step)
    world.wait_for_xmodule()
    world.edit_component()

    world.verify_setting_entry(
        world.get_setting_entry(DISPLAY_NAME),
        DISPLAY_NAME, '3.4', True
    )


@step('I can modify video display name')
def i_can_modify_video_display_name(_step):
    index = world.get_setting_entry_index(DISPLAY_NAME)
    world.set_field_value(index, '3.4')
    world.verify_setting_entry(world.get_setting_entry(DISPLAY_NAME), DISPLAY_NAME, '3.4', True)


@step('I upload transcript file(?:s)?:$')
def upload_transcript(step):
    input_hidden = '.metadata-video-translations .input'
    # Number of previously added translations
    initial_index = len(world.css_find(TRANSLATION_BUTTONS['download']))

    if step.hashes:
        for i, item in enumerate(step.hashes):
            lang_code = item['lang_code']
            filename = item['filename']
            index = initial_index + i

            choose_new_lang(lang_code)

            expected_text = world.css_text(TRANSLATION_BUTTONS['upload'], index=index)
            assert_equal(expected_text, "Upload")
            assert_equal(world.css_find(input_hidden).last.value, "")

            world.css_click(TRANSLATION_BUTTONS['upload'], index=index)
            success_upload_file(filename)

            world.wait_for_visible(TRANSLATION_BUTTONS['download'], index=index)
            assert_equal(world.css_find(TRANSLATION_BUTTONS['upload']).last.text, "Replace")
            assert_equal(world.css_find(input_hidden).last.value, filename)


@step('I try to upload transcript file "([^"]*)"$')
def try_to_upload_transcript(step, filename):
    world.css_click(TRANSLATION_BUTTONS['upload'])
    attach_file(filename, 'uploads/')


@step('I upload transcript file "([^"]*)" for "([^"]*)" language code$')
def upload_transcript_for_lang(step, filename, lang_code):
    get_xpath = lambda value: './/div/a[contains(@class, "upload-action")]'.format(value)
    container = get_setting_container(lang_code)

    # If translation isn't uploaded, prepare drop-down and try to find container again
    choose_new_lang(lang_code)
    container = get_setting_container(lang_code)

    button = container.find_by_xpath(get_xpath(lang_code)).first
    button.click()
    success_upload_file(filename)


@step('I replace transcript file for "([^"]*)" language code by "([^"]*)"$')
def replace_transcript_for_lang(step, lang_code, filename):
    get_xpath = lambda value: './/div/a[contains(@class, "upload-action")]'.format(value)
    container = get_setting_container(lang_code)

    button = container.find_by_xpath(get_xpath(lang_code)).first
    button.click()
    success_upload_file(filename)


@step('I see validation error "([^"]*)"$')
def verify_validation_error_message(step, error_message):
    assert_equal(world.css_text('#upload_error'), error_message)


@step('I can download transcript for "([^"]*)" language code, that contains text "([^"]*)"$')
def i_can_download_transcript(_step, lang_code, text):
    MIME_TYPE = 'application/x-subrip'
    get_xpath = lambda value: './/div/a[contains(text(), "Download")]'.format(value)
    container = get_setting_container(lang_code)
    assert container
    button = container.find_by_xpath(get_xpath(lang_code)).first
    url = button['href']
    request = RequestHandlerWithSessionId()
    assert_true(request.get(url).is_success())
    assert_true(request.check_header('content-type', MIME_TYPE))
    assert_in(text.encode('utf-8'), request.content)


@step('I remove translation for "([^"]*)" language code$')
def i_can_remove_transcript(_step, lang_code):
    get_xpath = lambda value: './/descendant::a[@data-lang="{}" and contains(@class,"remove-setting")]'.format(value)
    container = get_setting_container(lang_code)
    assert container
    button = container.find_by_xpath(get_xpath(lang_code)).first
    button.click()


@step('I see translations for "([^"]*)"$')
def verify_translations(_step, lang_codes_string):
    expected = [l.strip() for l in lang_codes_string.split(',')]
    actual = [l['data-lang'] for l in world.css_find('.metadata-video-translations .remove-setting')]
    assert_equal(set(expected), set(actual))


@step('I do not see translations$')
def no_translations(_step):
    assert_true(world.is_css_not_present('.metadata-video-translations .remove-setting'))


@step('I confirm prompt$')
def confirm_prompt(_step):
    world.confirm_studio_prompt()


@step('I (cannot )?choose "([^"]*)" language code$')
def i_choose_lang_code(_step, cannot, lang_code):
    choose_option(get_last_dropdown(), lang_code)
    if cannot:
        assert_not_equal(get_last_dropdown().value, lang_code, "Option with provided value was selected, but shouldn't")
    else:
        assert_equal(get_last_dropdown().value, lang_code, "Option with provided value is not available or was not selected")


@step('I click button "([^"]*)"$')
def click_button(_step, button):
    world.css_click(TRANSLATION_BUTTONS[button.lower()])


@step('video language menu has "([^"]*)" translations$')
def i_see_correct_langs(_step, langs):
    menu_name = 'language'
    open_menu(menu_name)
    items = world.css_find(VIDEO_MENUS[menu_name] + ' li')
    translations = {t.strip(): LANGUAGES[t.strip()] for t in langs.split(',')}

    assert_equal(len(translations), len(items))
    for lang_code, label in translations.items():
        assert_true(any([i.text == label for i in items]))
        assert_true(any([i['data-lang-code'] == lang_code for i in items]))


@step('video language with code "([^"]*)" at position "(\d+)"$')
def i_see_lang_at_position(_step, code, position):
    menu_name = 'language'
    open_menu(menu_name)
    item = world.css_find(VIDEO_MENUS[menu_name] + ' li')[int(position)]
    assert_equal(item['data-lang-code'], code)

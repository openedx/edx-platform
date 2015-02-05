# pylint: disable=missing-docstring

from lettuce import world, step
from selenium.webdriver.common.keys import Keys
from xmodule.modulestore.django import modulestore

VIDEO_BUTTONS = {
    'CC': '.hide-subtitles',
    'volume': '.volume',
    'play': '.video_control.play',
    'pause': '.video_control.pause',
    'handout': '.video-handout.video-download-button a',
}

SELECTORS = {
    'spinner': '.video-wrapper .spinner',
    'controls': 'section.video-controls',
}

# We should wait 300 ms for event handler invocation + 200ms for safety.
DELAY = 0.5


@step('youtube stub server (.*) YouTube API')
def configure_youtube_api(_step, action):
    action = action.strip()
    if action == 'proxies':
        world.youtube.config['youtube_api_blocked'] = False
    elif action == 'blocks':
        world.youtube.config['youtube_api_blocked'] = True
    else:
        raise ValueError('Parameter `action` should be one of "proxies" or "blocks".')


@step('I have created a Video component$')
def i_created_a_video_component(step):
    step.given('I am in Studio editing a new unit')
    world.create_component_instance(
        step=step,
        category='video',
    )

    world.wait_for_xmodule()
    world.disable_jquery_animations()

    world.wait_for_present('.is-initialized')
    world.wait(DELAY)
    world.wait_for_invisible(SELECTORS['spinner'])
    if not world.youtube.config.get('youtube_api_blocked'):
        world.wait_for_visible(SELECTORS['controls'])


@step('I have created a Video component with subtitles$')
def i_created_a_video_with_subs(_step):
    _step.given('I have created a Video component with subtitles "3_yD_cEKoCk"')


@step('I have created a Video component with subtitles "([^"]*)"$')
def i_created_a_video_with_subs_with_name(_step, sub_id):
    _step.given('I have created a Video component')

    # Store the current URL so we can return here
    video_url = world.browser.url

    # Upload subtitles for the video using the upload interface
    _step.given('I have uploaded subtitles "{}"'.format(sub_id))

    # Return to the video
    world.visit(video_url)

    world.wait_for_xmodule()

    # update .sub filed with proper subs name (which mimics real Studio/XML behavior)
    # this is needed only for that videos which are created in acceptance tests.
    _step.given('I edit the component')
    world.wait_for_ajax_complete()
    _step.given('I save changes')

    world.disable_jquery_animations()

    world.wait_for_present('.is-initialized')
    world.wait_for_invisible(SELECTORS['spinner'])


@step('I have uploaded subtitles "([^"]*)"$')
def i_have_uploaded_subtitles(_step, sub_id):
    _step.given('I go to the files and uploads page')
    _step.given('I upload the test file "subs_{}.srt.sjson"'.format(sub_id.strip()))


@step('when I view the (.*) it does not have autoplay enabled$')
def does_not_autoplay(_step, video_type):
    world.wait(DELAY)
    world.wait_for_ajax_complete()
    actual = world.css_find('.%s' % video_type)[0]['data-autoplay']
    expected = [u'False', u'false', False]
    assert actual in expected
    assert world.css_has_class('.video_control', 'play')


@step('creating a video takes a single click$')
def video_takes_a_single_click(_step):
    component_css = '.xmodule_VideoModule'
    assert world.is_css_not_present(component_css)

    world.css_click("a[data-category='video']")
    assert world.is_css_present(component_css)


@step('I edit the component$')
def i_edit_the_component(_step):
    world.edit_component()


@step('I have (hidden|toggled) captions$')
def hide_or_show_captions(step, shown):
    button_css = 'a.hide-subtitles'
    if shown == 'hidden':
        world.css_click(button_css)
    if shown == 'toggled':
        world.css_click(button_css)
        # When we click the first time, a tooltip shows up. We want to
        # click the button rather than the tooltip, so move the mouse
        # away to make it disappear.
        button = world.css_find(button_css)
        # mouse_out is not implemented on firefox with selenium
        if not world.is_firefox:
            button.mouse_out()
        world.css_click(button_css)


@step('I have created a video with only XML data$')
def xml_only_video(step):
    # Create a new video *without* metadata. This requires a certain
    # amount of rummaging to make sure all the correct data is present
    step.given('I have clicked the new unit button')

    # Wait for the new unit to be created and to load the page
    world.wait(1)

    course = world.scenario_dict['COURSE']
    store = modulestore()

    parent_location = store.get_items(course.id, qualifiers={'category': 'vertical'})[0].location

    youtube_id = 'ABCDEFG'
    world.scenario_dict['YOUTUBE_ID'] = youtube_id

    # Create a new Video component, but ensure that it doesn't have
    # metadata. This allows us to test that we are correctly parsing
    # out XML
    world.ItemFactory.create(
        parent_location=parent_location,
        category='video',
        data='<video youtube="1.00:%s"></video>' % youtube_id,
        modulestore=store,
        user_id=world.scenario_dict["USER"].id
    )


@step('The correct Youtube video is shown$')
def the_youtube_video_is_shown(_step):
    ele = world.css_find('.video').first
    assert ele['data-streams'].split(':')[1] == world.scenario_dict['YOUTUBE_ID']


@step('Make sure captions are (.+)$')
def set_captions_visibility_state(_step, captions_state):
    SELECTOR = '.closed .subtitles'
    world.wait_for_visible('.hide-subtitles')
    if captions_state == 'closed':
        if world.is_css_not_present(SELECTOR):
            world.css_find('.hide-subtitles').click()
    else:
        if world.is_css_present(SELECTOR):
            world.css_find('.hide-subtitles').click()


@step('I hover over button "([^"]*)"$')
def hover_over_button(_step, button):
    world.css_find(VIDEO_BUTTONS[button.strip()]).mouse_over()


@step('Captions (?:are|become) "([^"]*)"$')
def check_captions_visibility_state(_step, visibility_state):
    if visibility_state == 'visible':
        assert world.css_visible('.subtitles')
    else:
        assert not world.css_visible('.subtitles')


def find_caption_line_by_data_index(index):
    SELECTOR = ".subtitles > li[data-index='{index}']".format(index=index)
    return world.css_find(SELECTOR).first


@step('I focus on caption line with data-index "([^"]*)"$')
def focus_on_caption_line(_step, index):
    world.wait_for_present('.video.is-captions-rendered')
    world.wait_for(lambda _: world.css_text('.subtitles'), timeout=30)
    find_caption_line_by_data_index(int(index.strip()))._element.send_keys(Keys.TAB)


@step('I press "enter" button on caption line with data-index "([^"]*)"$')
def click_on_the_caption(_step, index):
    world.wait_for_present('.video.is-captions-rendered')
    world.wait_for(lambda _: world.css_text('.subtitles'), timeout=30)
    find_caption_line_by_data_index(int(index.strip()))._element.send_keys(Keys.ENTER)


@step('I see caption line with data-index "([^"]*)" has class "([^"]*)"$')
def caption_line_has_class(_step, index, className):
    SELECTOR = ".subtitles > li[data-index='{index}']".format(index=int(index.strip()))
    assert world.css_has_class(SELECTOR, className.strip())


@step('I see a range on slider$')
def see_a_range_slider_with_proper_range(_step):
    world.wait_for_visible(VIDEO_BUTTONS['pause'])
    assert world.css_visible(".slider-range")


@step('I (.*) see video button "([^"]*)"$')
def do_not_see_or_not_button_video(_step, action, button_type):
    world.wait(DELAY)
    world.wait_for_ajax_complete()
    action = action.strip()
    button = button_type.strip()
    if action == 'do not':
        assert not world.is_css_present(VIDEO_BUTTONS[button])
    elif action == 'can':
        assert world.css_visible(VIDEO_BUTTONS[button])
    else:
        raise ValueError('Parameter `action` should be one of "do not" or "can".')


@step('I click video button "([^"]*)"$')
def click_button_video(_step, button_type):
    world.wait(DELAY)
    world.wait_for_ajax_complete()
    button = button_type.strip()
    world.css_click(VIDEO_BUTTONS[button])


@step('I seek video to "([^"]*)" seconds$')
def seek_video_to_n_seconds(_step, seconds):
    time = float(seconds.strip())
    jsCode = "$('.video').data('video-player-state').videoPlayer.onSlideSeek({{time: {0:f}}})".format(time)
    world.browser.execute_script(jsCode)


@step('I see video starts playing from "([^"]*)" position$')
def start_playing_video_from_n_seconds(_step, position):
    world.wait_for(
        func=lambda _: world.css_html('.vidtime')[:4] == position.strip(),
        timeout=5
    )

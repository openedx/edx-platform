#pylint: disable=C0111

from lettuce import world, step
from xmodule.modulestore import Location
from contentstore.utils import get_modulestore
from selenium.webdriver.common.keys import Keys

VIDEO_BUTTONS = {
    'CC': '.hide-subtitles',
    'volume': '.volume',
    'play': '.video_control.play',
    'pause': '.video_control.pause',
}

SELECTORS = {
    'spinner': '.video-wrapper .spinner',
    'controls': 'section.video-controls',
}

# We should wait 300 ms for event handler invocation + 200ms for safety.
DELAY = 0.5


@step('I have created a Video component$')
def i_created_a_video_component(step):
    world.create_course_with_unit()
    world.create_component_instance(
        step=step,
        category='video',
    )

    world.wait_for_xmodule()
    world.disable_jquery_animations()

    world.wait_for_present('.is-initialized')
    world.wait(DELAY)
    world.wait_for_invisible(SELECTORS['spinner'])


@step('I have created a Video component with subtitles$')
def i_created_a_video_with_subs(_step):
    _step.given('I have created a Video component with subtitles "OEoXaMPEzfM"')


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
    world.disable_jquery_animations()

    world.wait_for_present('.is-initialized')
    world.wait_for_invisible(SELECTORS['spinner'])


@step('I have uploaded subtitles "([^"]*)"$')
def i_have_uploaded_subtitles(_step, sub_id):
    _step.given('I go to the files and uploads page')
    _step.given('I upload the test file "subs_{}.srt.sjson"'.format(sub_id.strip()))


@step('when I view the (.*) it does not have autoplay enabled$')
def does_not_autoplay(_step, video_type):
    assert world.css_find('.%s' % video_type)[0]['data-autoplay'] == 'False'
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

    location = world.scenario_dict['COURSE'].location
    store = get_modulestore(location)

    parent_location = store.get_items(Location(category='vertical', revision='draft'))[0].location

    youtube_id = 'ABCDEFG'
    world.scenario_dict['YOUTUBE_ID'] = youtube_id

    # Create a new Video component, but ensure that it doesn't have
    # metadata. This allows us to test that we are correctly parsing
    # out XML
    world.ItemFactory.create(
        parent_location=parent_location,
        category='video',
        data='<video youtube="1.00:%s"></video>' % youtube_id
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
        if not world.is_css_present(SELECTOR):
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
    find_caption_line_by_data_index(int(index.strip()))._element.send_keys(Keys.TAB)


@step('I press "enter" button on caption line with data-index "([^"]*)"$')
def click_on_the_caption(_step, index):
    find_caption_line_by_data_index(int(index.strip()))._element.send_keys(Keys.ENTER)


@step('I see caption line with data-index "([^"]*)" has class "([^"]*)"$')
def caption_line_has_class(_step, index, className):
    SELECTOR = ".subtitles > li[data-index='{index}']".format(index=int(index.strip()))
    assert world.css_has_class(SELECTOR, className.strip())


@step('I see a range on slider$')
def see_a_range_slider_with_proper_range(_step):
    world.wait_for_visible(VIDEO_BUTTONS['pause'])

    assert world.css_visible(".slider-range")


@step('I click video button "([^"]*)"$')
def click_button_video(_step, button_type):
    import ipdb; ipdb.set_trace()
    world.wait(DELAY)
    world.wait_for_ajax_complete()
    button = button_type.strip()
    world.css_click(VIDEO_BUTTONS[button])


#pylint: disable=C0111

from lettuce import world, step
from terrain.steps import reload_the_page
from xmodule.modulestore import Location
from contentstore.utils import get_modulestore


############### ACTIONS ####################

@step('I have created a Video component$')
def i_created_a_video_component(step):
    world.create_component_instance(
        step, '.large-video-icon',
        'video',
        '.xmodule_VideoModule',
        has_multiple_templates=False
    )


@step('I have created a Video component with subtitles$')
def i_created_a_video_component(step):
    step.given('I have created a Video component')

    # Store the current URL so we can return here
    video_url = world.browser.url

    # Upload subtitles for the video using the upload interface
    step.given('I have uploaded subtitles')

    # Return to the video
    world.visit(video_url)


@step('I have uploaded subtitles')
def i_have_uploaded_subtitles(step):
    step.given('I go to the files and uploads page')
    step.given('I upload the file "subs_OEoXaMPEzfM.srt.sjson"')


@step('when I view the (.*) it does not have autoplay enabled$')
def does_not_autoplay(_step, video_type):
    assert world.css_find('.%s' % video_type)[0]['data-autoplay'] == 'False'
    assert world.css_has_class('.video_control', 'play')


@step('creating a video takes a single click$')
def video_takes_a_single_click(_step):
    assert(not world.is_css_present('.xmodule_VideoModule'))
    world.css_click("a[data-category='video']")
    assert(world.is_css_present('.xmodule_VideoModule'))


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
    video = world.ItemFactory.create(
        parent_location=parent_location,
        category='video',
        data='<video youtube="1.00:%s"></video>' % youtube_id
    )

    # Refresh to see the new video
    reload_the_page(step)


@step('The correct Youtube video is shown$')
def the_youtube_video_is_shown(_step):
    ele = world.css_find('.video').first
    assert ele['data-streams'].split(':')[1] == world.scenario_dict['YOUTUBE_ID']


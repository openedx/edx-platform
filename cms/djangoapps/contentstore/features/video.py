# pylint: disable=missing-docstring

from lettuce import world, step

SELECTORS = {
    'spinner': '.video-wrapper .spinner',
    'controls': '.video-controls',
}

# We should wait 300 ms for event handler invocation + 200ms for safety.
DELAY = 0.5


@step('I have uploaded subtitles "([^"]*)"$')
def i_have_uploaded_subtitles(_step, sub_id):
    _step.given('I go to the files and uploads page')
    _step.given('I upload the test file "subs_{}.srt.sjson"'.format(sub_id.strip()))


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

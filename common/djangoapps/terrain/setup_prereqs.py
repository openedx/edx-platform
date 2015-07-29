"""
Set up the prequisites for acceptance tests.

This includes initialization and teardown for stub and video HTTP services
and checking for external URLs that need to be accessible and responding.

"""
from lettuce import before, after, world
from django.conf import settings
from terrain.stubs.youtube import StubYouTubeService
from terrain.stubs.xqueue import StubXQueueService
from terrain.stubs.lti import StubLtiService
from terrain.stubs.video_source import VideoSourceHttpService
from selenium.common.exceptions import NoAlertPresentException

import re
import requests

from logging import getLogger

LOGGER = getLogger(__name__)

SERVICES = {
    "youtube": {"port": settings.YOUTUBE_PORT, "class": StubYouTubeService},
    "xqueue": {"port": settings.XQUEUE_PORT, "class": StubXQueueService},
    "lti": {"port": settings.LTI_PORT, "class": StubLtiService},
}

YOUTUBE_API_URLS = {
    'main': 'https://www.youtube.com/',
    'player': 'https://www.youtube.com/iframe_api',
    # For transcripts, you need to check an actual video, so we will
    # just specify our default video and see if that one is available.
    'transcript': 'http://video.google.com/timedtext?lang=en&v=OEoXaMPEzfM',
}


@before.all  # pylint: disable=no-member
def start_video_server():
    """
    Serve the HTML5 Video Sources from a local port
    """
    video_source_dir = '{}/data/video'.format(settings.TEST_ROOT)
    video_server = VideoSourceHttpService(port_num=settings.VIDEO_SOURCE_PORT)
    video_server.config['root_dir'] = video_source_dir
    setattr(world, 'video_source', video_server)


@after.all  # pylint: disable=no-member
def stop_video_server(_total):
    """
    Stop the HTML5 Video Source server after all tests have executed
    """
    video_server = getattr(world, 'video_source', None)
    if video_server:
        video_server.shutdown()


@before.each_scenario  # pylint: disable=no-member
def process_requires_tags(scenario):
    """
    Process the scenario tags to make sure that any
    requirements are met prior to that scenario
    being executed.

    Scenario tags must be named with this convention:
    @requires_stub_bar, where 'bar' is the name of the stub service to start

    if 'bar' is 'youtube'
        if 'youtube' is not available Then
            DON'T start youtube stub server
            ALSO DON'T start any other stub server BECAUSE we will SKIP this Scenario so no need to start any stub
    else
        start the stub server

    """
    tag_re = re.compile('requires_stub_(?P<server>[^_]+)')
    for tag in scenario.tags:
        requires = tag_re.match(tag)

        if requires:
            if requires.group('server') == 'youtube':
                if not is_youtube_available(YOUTUBE_API_URLS):
                    # A hackish way to skip a test in lettuce as there is no proper way to skip a test conditionally
                    scenario.steps = []
                    return

            start_stub(requires.group('server'))


def start_stub(name):
    """
    Start the required stub service running on a local port.
    Since these services can be reconfigured on the fly,
    we start them on a scenario basis when needed and
    stop them at the end of the scenario.
    """
    service = SERVICES.get(name, None)
    if service:
        fake_server = service['class'](port_num=service['port'])
        setattr(world, name, fake_server)


def is_youtube_available(urls):
    """
    Check if the required youtube urls are available.
    If they are not, then skip the scenario.
    """
    for name, url in urls.iteritems():
        try:
            response = requests.get(url, allow_redirects=False)
        except requests.exceptions.ConnectionError:
            LOGGER.warning("Connection Error. YouTube {0} service not available. Skipping this test.".format(name))
            return False

        status = response.status_code
        if status >= 300:
            LOGGER.warning(
                "YouTube {0} service not available. Status code: {1}. Skipping this test.".format(name, status))

            # No need to check all the URLs
            return False

    return True


@after.each_scenario  # pylint: disable=no-member
def stop_stubs(_scenario):
    """
    Shut down any stub services that were started up for the scenario.
    """
    for name in SERVICES.keys():
        stub_server = getattr(world, name, None)
        if stub_server is not None:
            stub_server.shutdown()


@after.each_scenario  # pylint: disable=no-member
def clear_alerts(_scenario):
    """
    Clear any alerts that might still exist, so that
    the next scenario will not fail due to their existence.

    Note that the splinter documentation indicates that
    get_alert should return None if no alert is present,
    however that is not the case. Instead a
    NoAlertPresentException is raised.
    """
    try:
        with world.browser.get_alert() as alert:
            alert.dismiss()
    except NoAlertPresentException:
        pass

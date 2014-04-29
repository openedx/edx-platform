"""
Initialize and teardown stub and video HTTP services for use in acceptance tests.
"""
from lettuce import before, after, world
from django.conf import settings
from terrain.stubs.youtube import StubYouTubeService
from terrain.stubs.xqueue import StubXQueueService
from terrain.stubs.lti import StubLtiService
from terrain.stubs.video_source import VideoSourceHttpService


SERVICES = {
    "youtube": {"port": settings.YOUTUBE_PORT, "class": StubYouTubeService},
    "xqueue": {"port": settings.XQUEUE_PORT, "class": StubXQueueService},
    "lti": {"port": settings.LTI_PORT, "class": StubLtiService},
}


@before.all  # pylint: disable=E1101
def start_video_server():
    """
    Serve the HTML5 Video Sources from a local port
    """
    video_source_dir = '{}/data/video'.format(settings.TEST_ROOT)
    video_server = VideoSourceHttpService(port_num=settings.VIDEO_SOURCE_PORT)
    video_server.config['root_dir'] = video_source_dir
    setattr(world, 'video_source', video_server)


@after.all  # pylint: disable=E1101
def stop_video_server(_total):
    """
    Stop the HTML5 Video Source server after all tests have executed
    """
    video_server = getattr(world, 'video_source', None)
    if video_server:
        video_server.shutdown()


@before.each_scenario
def start_stubs(_scenario):
    """
    Start each stub service running on a local port.
    Since these services can be reconfigured on the fly,
    stop and restart them on a scenario basis.
    """
    for name, service in SERVICES.iteritems():
        fake_server = service['class'](port_num=service['port'])
        setattr(world, name, fake_server)


@after.each_scenario
def stop_stubs(_scenario):
    """
    Shut down each stub service.
    """
    for name in SERVICES.keys():
        stub_server = getattr(world, name, None)
        if stub_server is not None:
            stub_server.shutdown()

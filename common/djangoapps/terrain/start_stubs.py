"""
Initialize and teardown fake HTTP services for use in acceptance tests.
"""

from lettuce import before, after, world
from django.conf import settings
from terrain.stubs.youtube import StubYouTubeService
from terrain.stubs.xqueue import StubXQueueService


SERVICES = {
    "youtube": {"port": settings.YOUTUBE_PORT, "class": StubYouTubeService},
    "xqueue": {"port": settings.XQUEUE_PORT, "class": StubXQueueService},
}


@before.all
def start_stubs():
    """
    Start each stub service running on a local port.
    """
    for name, service in SERVICES.iteritems():
        fake_server = service['class'](port_num=service['port'])
        setattr(world, name, fake_server)


@after.all
def stop_stubs(_):
    """
    Shut down each stub service.
    """
    for name in SERVICES.keys():
        stub_server = getattr(world, name, None)
        if stub_server is not None:
            stub_server.shutdown()

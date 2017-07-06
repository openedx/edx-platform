"""
Command-line utility to start a stub service.
"""
import sys
import time
import logging

from .comments import StubCommentsService
from .ecommerce import StubEcommerceService
from .xqueue import StubXQueueService
from .youtube import StubYouTubeService
from .lti import StubLtiService
from .video_source import VideoSourceHttpService
from .edxnotes import StubEdxNotesService
from .programs import StubProgramsService


USAGE = "USAGE: python -m stubs.start SERVICE_NAME PORT_NUM [CONFIG_KEY=CONFIG_VAL, ...]"

SERVICES = {
    'xqueue': StubXQueueService,
    'youtube': StubYouTubeService,
    'comments': StubCommentsService,
    'lti': StubLtiService,
    'video': VideoSourceHttpService,
    'edxnotes': StubEdxNotesService,
    'programs': StubProgramsService,
    'ecommerce': StubEcommerceService,
}

# Log to stdout, including debug messages
logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(message)s")


def get_args():
    """
    Parse arguments, returning tuple of `(service_name, port_num, config_dict)`.
    Exits with a message if arguments are invalid.
    """
    if len(sys.argv) < 3:
        print USAGE
        sys.exit(1)

    service_name = sys.argv[1]
    port_num = sys.argv[2]
    config_dict = _parse_config_args(sys.argv[3:])

    if service_name not in SERVICES:
        print "Unrecognized service '{0}'.  Valid choices are: {1}".format(
            service_name, ", ".join(SERVICES.keys()))
        sys.exit(1)

    try:
        port_num = int(port_num)
        if port_num < 0:
            raise ValueError

    except ValueError:
        print "Port '{0}' must be a positive integer".format(port_num)
        sys.exit(1)

    return service_name, port_num, config_dict


def _parse_config_args(args):
    """
    Parse stub configuration arguments, which are strings of the form "KEY=VAL".
    `args` is a list of arguments from the command line.
    Any argument that does not match the "KEY=VAL" format will be logged and skipped.

    Returns a dictionary with the configuration keys and values.
    """
    config_dict = dict()
    for config_str in args:
        try:
            components = config_str.split('=')
            if len(components) >= 2:
                config_dict[components[0]] = "=".join(components[1:])

        except:
            print "Warning: could not interpret config value '{0}'".format(config_str)
            pass

    return config_dict


def main():
    """
    Start a server; shut down on keyboard interrupt signal.
    """
    service_name, port_num, config_dict = get_args()
    print "Starting stub service '{0}' on port {1}...".format(service_name, port_num)

    server = SERVICES[service_name](port_num=port_num)
    server.config.update(config_dict)

    try:
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print "Stopping stub service..."

    finally:
        server.shutdown()


if __name__ == "__main__":
    main()

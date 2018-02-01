from channels.routing import route, route_class
from channels.staticfiles import StaticFilesConsumer
from lms.djangoapps.completion import consumers

# routes defined for channel calls
# this is similar to the Django urls, but specifically for Channels
channel_routing = [
    route_class(consumers.CompletionConsumer, path=r"^/completion_status/"),
]
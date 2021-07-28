"""
This module handles the detection of crawlers, so that we can handle them
appropriately in other parts of the code.
"""


from config_models.models import ConfigurationModel
from django.db import models


class CrawlersConfig(ConfigurationModel):
    """
    Configuration for the crawlers django app.

    .. no_pii:
    """
    class Meta:
        app_label = "crawlers"

    known_user_agents = models.TextField(
        blank=True,
        help_text="A comma-separated list of known crawler user agents.",
        default='edX-downloader',
    )

    def __str__(self):
        return f'CrawlersConfig("{self.known_user_agents}")'

    @classmethod
    def is_crawler(cls, request):
        """Determine if the request came from a crawler or not.

        This method is simplistic and only looks at the user agent header at the
        moment, but could later be improved to be smarter about detection.
        """
        current = cls.current()
        if not current.enabled:
            return False

        req_user_agent = request.META.get('HTTP_USER_AGENT')
        crawler_agents = current.known_user_agents.split(",")

        # If there was no user agent detected or no crawler agents configured,
        # then just return False.
        if (not req_user_agent) or (not crawler_agents):
            return False

        # The crawler_agents list we pull from our model always has unicode objects, but the
        # req_user_agent we get from HTTP headers ultimately comes to us via WSGI. That
        # value is an ISO-8859-1 encoded byte string in Python 2.7 (and in the HTTP spec), but
        # it will be a unicode str when we move to Python 3.x. This code should work under
        # either version.
        if isinstance(req_user_agent, bytes):
            crawler_agents = [crawler_agent.encode('iso-8859-1') for crawler_agent in crawler_agents]

        # We perform prefix matching of the crawler agent here so that we don't
        # have to worry about version bumps.
        return any(
            req_user_agent.startswith(crawler_agent)
            for crawler_agent in crawler_agents
        )

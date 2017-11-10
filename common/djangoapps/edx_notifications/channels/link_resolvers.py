"""
File containing link resolvers
"""

from importlib import import_module
import logging
import abc

from edx_notifications.data import NotificationMessage

log = logging.getLogger(__name__)


class BaseLinkResolver(object):
    """
    The abstract base class that all link resolvers will need to implement
    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def resolve(self, msg_type_name, link_name, params, exact_match_only=False):
        """
        Takes a msg, link_name, and a set of dictionary params
        and returns a URL path
        """
        raise NotImplementedError()


class MsgTypeToUrlLinkResolver(BaseLinkResolver):
    """
    This resolver will convert a msg-type to a URL through
    static mappings defined in our settings configuration
    """

    def __init__(self, mappings):
        """
        Initializer. Mappings will include all the
        statically defined URL mappings
        """

        self.mappings = mappings

    def resolve(self, msg_type_name, link_name, params, exact_match_only=False):
        """
        Takes a msg, link_name, and a set of dictionary params
        and returns a URL path
        """

        # do we have this link name?
        if link_name not in self.mappings:
            return None

        maps = self.mappings[link_name]

        # do we have this msg-type? First look for exact map
        # and then work upwards in wildcard cope

        search_name = msg_type_name

        mapping = maps.get(search_name)
        if not mapping and not exact_match_only:
            #
            # We support hierarchies of mappings so that
            # msg_types that are similar can all point to the
            # same URL
            #
            search_name, __, __ = search_name.rpartition('.')

            # loop over all possible wildcards throughout the namespace
            # from most specific to generic
            while not mapping and search_name:
                mapping = maps.get(search_name + '.*')
                if not mapping:
                    search_name, __, __ = search_name.rpartition('.')

            if not mapping:
                if '*' in maps:
                    mapping = maps['*']

        if not mapping:
            # coulnd't find any match, so say that we don't have a type to URL resolver
            return None

        try:
            return mapping.format(**params)  # pylint:disable=star-args
        except KeyError, ex:
            err_msg = (
                'TypeToURLResolver: attempted to resolve link_name "{link_name}" '
                'for msg_type "{msg_type}" with string "{format_string}" and '
                'parameters "{params}, but got KeyError: "{ex_msg}"! Check the configuration '
                'and caller!'
            ).format(
                link_name=link_name,
                msg_type=msg_type_name,
                format_string=mapping,
                params=params,
                ex_msg=str(ex)
            )
            log.error(err_msg)
            # simply continue by returning None. Upstream will consider this as
            # not resolvable
            return None


class MsgTypeToUrlResolverMixin(object):
    """
    Helper mix-in class to share logic when channels need to use
    similar link resolvers
    """

    _cached_resolvers = {}

    def _get_linked_resolved_msg(self, msg):
        """
        This helper will attempt to resolve all
        links that are present in the message

        resolve any links that may need conversion into URL paths
        This uses a subdict named "_resolve_links" in the msg.resolve_links
        field:

            resolve_links = {
                "_resolve_links": {
                    "_click_link": {
                       "param1": "val1",
                       "param2": "param2"
                    },
                    :
                },
             :
            }

        This above will try to resolve the URL for the link named "_click_link" (for
        example, when a user clicks on a notification, the should go to that URL), with the
        URL parameters "param1"="val1" and "param2"="val2", and put that link name back in
        the main payload dictionary as "_click_link"
        """

        if msg.resolve_links:
            for link_name, link_params in msg.resolve_links.iteritems():
                resolved_link = self.resolve_msg_link(msg, link_name, link_params)
                if resolved_link:
                    # copy the msg because we are going to alter it and we don't want to affect
                    # the passed in version
                    msg = NotificationMessage.clone(msg)

                    # if we could resolve, then store the resolved link in the payload itself
                    msg.payload[link_name] = resolved_link

        # return the msg which could be a clone of the original one
        return msg

    def _get_link_resolver(self, resolver_name):
        """
        Returns a link resolver class from the name
        """

        # see if we have a cached resolver as it should be a singleton

        if resolver_name in self._cached_resolvers:
            return self._cached_resolvers[resolver_name]

        resolver = None
        if self.link_resolvers and resolver_name in self.link_resolvers:
            # need to have link_resolvers defined in our channel options config
            if 'class' in self.link_resolvers[resolver_name]:
                _class_name = self.link_resolvers[resolver_name]['class']
                config = {}
                if 'config' in self.link_resolvers[resolver_name]:
                    config = self.link_resolvers[resolver_name]['config']

                # now create an instance of the resolver
                module_path, _, name = _class_name.rpartition('.')
                class_ = getattr(import_module(module_path), name)
                resolver = class_(config)  # pylint: disable=star-args

                # put in our cache
                self._cached_resolvers[resolver_name] = resolver

        return resolver

    def resolve_msg_link(self, msg, link_name, params, channel_context=None):  # pylint: disable=unused-argument
        """
        This implements the interface method for NotificationChannelProvier.
        Generates the appropriate link given a msg, a link_name, and params
        """

        # right now we just support resolution through
        # type_name -> key lookups, aka 'type_to_url' in our
        # link_resolvers config dict. This is reserved for
        # future extension
        resolver = self._get_link_resolver('msg_type_to_url')

        resolved_link = None
        if resolver:
            resolved_link = resolver.resolve(msg.msg_type.name, link_name, params)

        return resolved_link

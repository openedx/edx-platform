import logging
from channels import Group
from channels.sessions import channel_session
from channels.auth import channel_session_user
from channels.generic.websockets import JsonWebsocketConsumer

log = logging.getLogger(__name__)


class CompletionConsumer(JsonWebsocketConsumer):
    # Set to True to automatically port users from HTTP cookies
    # (you don't need channel_session_user, this implies it)
    http_user = True

    def connection_groups(self, **kwargs):
        """
        Called to return the list of groups to automatically add/remove
        this connection to/from.
        """
        # TODO: this should be connection_group per user, so we're not sending all completion to all users
        # Need to figure out how to get message.user at this time
        return ["completion"]

    def connect(self, message, **kwargs):
        """
        Perform things on connection start
        """
        self.message.reply_channel.send({"accept": True})
        pass

    def receive(self, content, **kwargs):
        """
        Called when a message is received with either text or bytes
        filled out.
        """
        pass
    
    def disconnect(self, message, **kwargs):
        """
        Perform things on connection close
        """
        pass
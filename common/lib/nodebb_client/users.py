from logging import getLogger
from pynodebb.api.users import User

log = getLogger(__name__)


class ForumUser(User):

    def join(self, group_name, user_name, uid=1, **kwargs):
        payload = {'name': group_name, 'username': user_name, '_uid': uid}
        log.info("payload %s" % payload)
        return self.client.post('/api/v2/users/join', **payload)

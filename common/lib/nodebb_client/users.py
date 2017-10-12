from pynodebb.api.users import User


class ForumUser(User):

    def join(self, group_name, user_name, uid=1, **kwargs):
        payload = {'name': group_name, 'username': user_name, '_uid': uid}
        return self.client.post('/api/v2/users/join', **payload)

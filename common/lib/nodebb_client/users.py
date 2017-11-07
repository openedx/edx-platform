from pynodebb.api.users import User


class ForumUser(User):
    def join(self, group_name, user_name, uid=1, **kwargs):
        payload = {'name': group_name, 'username': user_name, '_uid': uid}
        return self.client.post('/api/v2/users/join', **payload)

    def create(self, username, **kwargs):
        kwargs.update({'username': username})
        return self.client.post('/api/v2/users/create', **kwargs['kwargs'])

    def activate(self, username, **kwargs):
        payload = {'username': username}
        return self.client.post('/api/v2/users/activate', **payload)

    def update_profile(self, username, **kwargs):
        kwargs['kwargs']['username'] = username
        return self.client.post('/api/v2/users/update', **kwargs['kwargs'])

from requests.exceptions import ConnectionError

from pynodebb.api.users import User


class ForumUser(User):
    """
    Added custom methods to the default User class of pynodebb package
    """

    def join(self, group_name, username, uid=1):
        """
        Make user a participant of specified group
        """
        payload = {'name': group_name, 'username': username, '_uid': uid}
        return self.client.post('/api/v2/users/join', **payload)

    def create(self, username, user_data):
        """
        Create a user on Nodebb
        @param: username - str
        @param: user_data - dict
        """
        user_data['username'] = username
        return self.client.post('/api/v2/users/create', **user_data)

    def activate(self, username, active):
        """
        Activate a given user
        """
        payload = {'username': username, 'active': active, "_uid": 1}
        return self.client.post('/api/v2/users/activate', **payload)

    def update_profile(self, username, profile_data):
        """
        Updated user profile by providing fields in kwargs
        """
        profile_data['username'] = username
        return self.client.post('/api/v2/users/update', **profile_data)

    def delete_user(self, username):
        """
        Delete user from NodBB database
        """
        payload = {
            'username': username,
            '_uid': 1
        }
        return self.client.delete('/api/v2/user/delete', **payload)

    def update_onboarding_surveys_status(self, username):
        """
        Update NodeBB when user successfully completed all required onboarding surveys
        """
        return self.client.get('/api/v2/users/update-visibility-status?username={}'.format(username))

    def all(self):
        """
        Returns and array of all users present on NodeBB
        """
        return self.client.post('/api/v2/users/all')

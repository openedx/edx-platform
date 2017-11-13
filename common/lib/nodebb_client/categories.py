from pynodebb.api.categories import Category


class ForumCategory(Category):

    def create(self, name, hidden=1, uid=1, **kwargs):
        payload = {'name': name, '_uid': uid, 'hidden': hidden}
        return self.client.post('/api/v2/category/private', **payload)

    def featured(self, **kwargs):
        return self.client.get('/api/v2/category/featured', **kwargs)

    def recommended(self, username, **kwargs):
        payload = {'username': username}
        return self.client.post('/api/v2/category/recommended', **payload)

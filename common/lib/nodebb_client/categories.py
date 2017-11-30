from pynodebb.api.categories import Category


class ForumCategory(Category):
    """
    Added custom methods to the default Category class of pynodebb package
    """

    def create(self, name, hidden=1, uid=1, **kwargs):
        """
         Create a private category on NodeBB
        """
        payload = {'name': name, '_uid': uid, 'hidden': hidden}
        return self.client.post('/api/v2/category/private', **payload)

    def featured(self, **kwargs):
        """
        Get all the featured categories from NodeBB
        """
        return self.client.get('/api/v2/category/featured', **kwargs)

    def recommended(self, username, **kwargs):
        """
        Get recommended categories for a specific user
        """
        payload = {'username': username}
        return self.client.post('/api/v2/category/recommended', **payload)

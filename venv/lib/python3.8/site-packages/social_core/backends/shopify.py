"""
Shopify OAuth2 backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/shopify.html
"""
import imp

from ..exceptions import AuthCanceled, AuthFailed
from ..utils import handle_http_errors
from .oauth import BaseOAuth2


class ShopifyOAuth2(BaseOAuth2):
    """Shopify OAuth2 authentication backend"""
    name = 'shopify'
    ID_KEY = 'shop'
    EXTRA_DATA = [
        ('shop', 'shop'),
        ('website', 'website'),
        ('expires', 'expires')
    ]
    REDIRECT_STATE = False

    @property
    def shopify_api_version(self):
        return self.setting('API_VERSION', '2020-10')

    @property
    def shopify_api(self):
        if not hasattr(self, '_shopify_api'):
            fp, pathname, description = imp.find_module('shopify')
            self._shopify_api = imp.load_module('shopify', fp, pathname,
                                                description)
        return self._shopify_api

    def get_user_details(self, response):
        """Use the shopify store name as the username"""
        return {
            'username': str(response.get('shop', '')).replace(
                '.myshopify.com', ''
            )
        }

    def extra_data(self, user, uid, response, details=None, *args, **kwargs):
        """Return access_token and extra defined names to store in
        extra_data field"""
        data = super().extra_data(user, uid, response, details, *args, **kwargs)
        session = self.shopify_api.Session(self.data.get('shop').strip(),
                                           version=self.shopify_api_version)
        # Get, and store the permanent token
        token = session.request_token(data['access_token'])
        data['access_token'] = token
        return dict(data)

    def auth_url(self):
        key, secret = self.get_key_and_secret()
        self.shopify_api.Session.setup(api_key=key, secret=secret)
        scope = self.get_scope()
        state = self.state_token()
        self.strategy.session_set(self.name + '_state', state)
        redirect_uri = self.get_redirect_uri(state)
        session = self.shopify_api.Session(self.data.get('shop').strip(),
                                           version=self.shopify_api_version)
        return session.create_permission_url(
            scope=scope,
            redirect_uri=redirect_uri
        )

    @handle_http_errors
    def auth_complete(self, *args, **kwargs):
        """Completes login process, must return user instance"""
        self.process_error(self.data)
        access_token = None
        key, secret = self.get_key_and_secret()
        try:
            shop_url = self.data.get('shop')
            self.shopify_api.Session.setup(api_key=key, secret=secret)
            shopify_session = self.shopify_api.Session(
                shop_url, version=self.shopify_api_version, token=self.data
            )
            access_token = shopify_session.token
        except self.shopify_api.ValidationException:
            raise AuthCanceled(self)
        else:
            if not access_token:
                raise AuthFailed(self, 'Authentication Failed')
        return self.do_auth(access_token, shop_url, shopify_session.url,
                            *args, **kwargs)

    def do_auth(self, access_token, shop_url, website, *args, **kwargs):
        kwargs.update({
            'backend': self,
            'response': {
                'shop': shop_url,
                'website': f'http://{website}',
                'access_token': access_token
            }
        })
        return self.strategy.authenticate(*args, **kwargs)

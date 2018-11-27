# -*- coding: utf-8 -*-
# author:duoduo3369@gmail.com  https://github.com/duoduo369
# modified by sodaling for weixin app login
"""
Weixin OAuth2 backend
"""
import urllib
from requests import HTTPError

from social_core.backends.oauth import BaseOAuth2
from social_core.exceptions import AuthCanceled, AuthUnknownError


class WeixinOAuth2(BaseOAuth2):
    """Weixin OAuth authentication backend"""
    name = 'weixin'
    ID_KEY = 'unionid'
    AUTHORIZATION_URL = 'https://open.weixin.qq.com/connect/qrconnect'
    ACCESS_TOKEN_URL = 'https://api.weixin.qq.com/sns/oauth2/access_token'
    ACCESS_TOKEN_METHOD = 'POST'
    DEFAULT_SCOPE = ['snsapi_login']
    REDIRECT_STATE = False
    EXTRA_DATA = [
        ('nickname', 'username'),
        ('headimgurl', 'profile_image_url'),
    ]

    def get_user_details(self, response):
        """Return user details from Weixin. API URL is:
        https://api.weixin.qq.com/sns/userinfo
        """
        if self.setting('DOMAIN_AS_USERNAME'):
            username = response.get('domain', '')
        else:
            username = response.get('nickname', '')
        return {
            'username': username,
            'profile_image_url': response.get('headimgurl', '')
        }

    def user_data(self, access_token, *args, **kwargs):
        data = self.get_json('https://api.weixin.qq.com/sns/userinfo', params={
            'access_token': access_token,
            'openid': kwargs.get('response', {}).get('openid') or kwargs.get('openid', 'null')
        })

        nickname = data.get('nickname')
        if nickname:
            # weixin api has some encode bug, here need handle
            data['nickname'] = nickname.encode(
                'raw_unicode_escape'
            ).decode('utf-8')
        return data

    def auth_params(self, state=None):
        appid, secret = self.get_key_and_secret()
        params = {
            'appid': appid,
            'redirect_uri': self.get_redirect_uri(state)
        }
        if self.STATE_PARAMETER and state:
            params['state'] = state
        if self.RESPONSE_TYPE:
            params['response_type'] = self.RESPONSE_TYPE
        return params

    def auth_complete_params(self, state=None):
        appid, secret = self.get_key_and_secret()
        return {
            'grant_type': 'authorization_code',  # request auth code
            'code': self.data.get('code', ''),  # server response code
            'appid': appid,
            'secret': secret,
            'redirect_uri': self.get_redirect_uri(state)
        }

    def refresh_token_params(self, token, *args, **kwargs):
        appid, secret = self.get_key_and_secret()
        return {
            'refresh_token': token,
            'grant_type': 'refresh_token',
            'appid': appid,
            'secret': secret
        }

    def auth_complete(self, *args, **kwargs):
        """Completes loging process, must return user instance"""
        self.process_error(self.data)
        try:
            response = self.request_access_token(
                self.ACCESS_TOKEN_URL,
                data=self.auth_complete_params(self.validate_state()),
                headers=self.auth_headers(),
                method=self.ACCESS_TOKEN_METHOD
            )
        except HTTPError as err:
            if err.response.status_code == 400:
                raise AuthCanceled(self, response=err.response)
            else:
                raise
        except KeyError:
            raise AuthUnknownError(self)
        if 'errcode' in response:
            raise AuthCanceled(self)
        self.process_error(response)
        return self.do_auth(response['access_token'], response=response,
                            *args, **kwargs)


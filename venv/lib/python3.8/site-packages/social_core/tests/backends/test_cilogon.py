import json

from .oauth import OAuth2Test


class CILogonOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.cilogon.CILogonOAuth2'
    user_data_url = 'https://cilogon.org/oauth2/userinfo'
    user_data_url_post = True
    expected_username = 'jbasney@illinois.edu'
    access_token_body = json.dumps({
        'access_token':'https://cilogon.org/oauth2/accessToken/sample-token123',
        'refresh_token':'https://cilogon.org/oauth2/refreshToken/sample123/refresh-token123',
        'id_token':'aBigStringOfRandomChars.123abc',
        'token_type':'Bearer',
        'expires_in':900
    })
    user_data_body = json.dumps({
        'sub':'http://cilogon.org/serverA/users/534',
        'idp_name':'University of Illinois at Urbana-Champaign',
        'idp':'urn:mace:incommon:uiuc.edu',
        'affiliation':'employee@illinois.edu;member@illinois.edu;staff@illinois.edu',
        'eppn':'jbasney@illinois.edu',
        'eptid':'urn:mace:incommon:uiuc.edu!https://cilogon.org/shibboleth!cyXC3O5fi0t1NBsW1NsOxZDyDd4=',
        'name':'James Alan Basney',
        'given_name':'James',
        'family_name':'Basney',
        'email':'jbasney@illinois.edu'
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()
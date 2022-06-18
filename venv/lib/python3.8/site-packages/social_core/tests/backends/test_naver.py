import json

from .oauth import OAuth2Test


class NaverOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.naver.NaverOAuth2'
    user_data_url = 'https://openapi.naver.com/v1/nid/me'
    expected_username = 'foobar'
    access_token_body = json.dumps({
        'access_token': 'foobar',
        'token_type': 'bearer',
    })

    user_data_content_type = 'text/json'
    user_data_body = json.dumps({
        'resultcode': '00',
        'message': 'success',
        'response': {
            'email': 'openapi@naver.com',
            'nickname': 'foobar',
            'profile_image': 'https://ssl.pstatic.net/static/pwe/address/nodata_33x33.gif',
            'age': '40-49',
            'gender': 'F',
            'id': '32742776',
            'name': 'foobar',
            'birthday': '10-01',
        }
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()

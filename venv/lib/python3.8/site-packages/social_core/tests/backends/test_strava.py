import json

from .oauth import OAuth2Test


class StravaOAuthTest(OAuth2Test):
    backend_path = 'social_core.backends.strava.StravaOAuth'
    user_data_url = 'https://www.strava.com/api/v3/athlete'
    expected_username = 'marianne_v'
    access_token_body = json.dumps({
        'token_type': 'Bearer',
        'expires_at': 1572805000,
        'expires_in': 227615,
        'refresh_token': 'f51defab4632d27255dd0d106504dfd7568fd1df6',
        'access_token': '83ebeabdec09f6670863766f792ead24d61fe3f9',
        'athlete': {
            'id': 1234567890987654321,
            'username': 'marianne_v',
            'resource_state': 2,
            'firstname': 'Marianne',
            'lastname': 'V.',
            'city': 'Francisco',
            'state': 'California',
            'country': 'United States',
            'sex': 'F',
            'premium': 'true',
            'summit': 'true',
            'created_at': '2017-11-14T02:30:05Z',
            'updated_at': '2018-02-06T19:32:20Z',
            'badge_type_id': 4,
            'profile_medium': 'https://xxxxxx.cloudfront.net/pictures/athletes/123456789/123456789/2/medium.jpg',
            'profile': 'https://xxxxx.cloudfront.net/pictures/athletes/123456789/123456789/2/large.jpg',
            'friend': 'null',
            'follower': 'null'
        }
    })
    user_data_body = json.dumps({
        'id': 1234567890987654321,
        'username': 'marianne_v',
        'resource_state': 3,
        'firstname': 'Marianne',
        'lastname': 'V.',
        'city': 'San Francisco',
        'state': 'CA',
        'country': 'US',
        'sex': 'F',
        'premium': 'true',
        'created_at': '2017-11-14T02:30:05Z',
        'updated_at': '2018-02-06T19:32:20Z',
        'badge_type_id': 4,
        'profile_medium': 'https://xxxxxx.cloudfront.net/pictures/athletes/123456789/123456789/2/medium.jpg',
        'profile': 'https://xxxxx.cloudfront.net/pictures/athletes/123456789/123456789/2/large.jpg',
        'friend': 'null',
        'follower': 'null',
        'follower_count': 5,
        'friend_count': 5,
        'mutual_friend_count': 0,
        'athlete_type': 1,
        'date_preference': '%m/%d/%Y',
        'measurement_preference': 'feet',
        'clubs': [],
        'ftp': 'null',
        'weight': 0,
        'bikes': [],
        'shoes': []
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()

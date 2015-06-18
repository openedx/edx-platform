import os

AUTH_USER =os.environ['AUTH_USER_NAME']
AUTH_PASS =os.environ['AUTH_PASS_WORD']

BASE_URL = 'https://' + AUTH_USER + ':' + AUTH_PASS + '@courses.stage.edx.org'
BASE_URL_PREVIEW = 'https://' + AUTH_USER + ':' + AUTH_PASS + '@preview.stage.edx.org'

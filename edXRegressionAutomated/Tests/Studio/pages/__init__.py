__author__ = 'mac'
import os

AUTH_USER =os.environ['AUTH_USER_NAME']
AUTH_PASS =os.environ['AUTH_PASS_WORD']

BASE_URL = 'https://' + AUTH_USER + ':' + AUTH_PASS + '@studio.stage.edx.org'



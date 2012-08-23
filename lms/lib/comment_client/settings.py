from django.conf import settings

if hasattr(settings, "COMMENTS_SERVICE_URL"):
    SERVICE_HOST = settings.COMMENTS_SERVICE_URL
else:
    SERVICE_HOST = 'http://localhost:4567'

PREFIX = SERVICE_HOST + '/api/v1'

if hasattr(settings, "COMMENTS_SERVICE_KEY"):
    API_KEY = settings.COMMENTS_SERVICE_KEY
else:
    API_KEY = "PUT_YOUR_API_KEY_HERE"

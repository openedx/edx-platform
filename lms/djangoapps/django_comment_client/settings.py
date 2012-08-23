from django.conf import settings

MAX_COMMENT_DEPTH = None

if hasattr(settings, 'DISCUSSION_SETTINGS'):
    MAX_COMMENT_DEPTH = settings.DISCUSSION_SETTINGS.get('MAX_COMMENT_DEPTH')

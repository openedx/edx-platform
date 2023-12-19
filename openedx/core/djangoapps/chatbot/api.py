from .utils import get_site_config
from django.conf import settings

LMS_BASE = getattr(settings, 'LMS_BASE', 'localhost:18000')
CHATBOT_BEARER_TOKEN = get_site_config(LMS_BASE, 'CHATBOT_BEARER_TOKEN','ed40c0c1a649f6c8490ded9f72c4d616')
CHATBOT_QUERY_API = get_site_config(LMS_BASE, 'CHATBOT_QUERY_API', 'http://172.188.64.77:8000/v00/chat')



from .utils import get_site_config
from django.conf import settings

def get_chatbot_bearer_token():
    lms_domain =getattr(settings, 'LMS_BASE', 'localhost:18000')
    return get_site_config(lms_domain, 'CHATBOT_BEARER_TOKEN', 'ed40c0c1a649f6c8490ded9f72c4d616')

def get_chatbot_api_url():
    lms_domain =getattr(settings, 'LMS_BASE', 'localhost:18000')
    return get_site_config(lms_domain, 'CHATBOT_QUERY_API', 'http://172.188.64.77:8000/v00/chat')

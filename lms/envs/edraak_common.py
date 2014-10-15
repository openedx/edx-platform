# -*- coding: utf-8 -*-
from .aws import FEATURES

FEATURES['ENABLE_DISCUSSION_HOME_PANEL'] = False
FEATURES['AUTH_USE_OPENID_PROVIDER'] = True

FILE_UPLOAD_STORAGE_BUCKET_NAME = "edraak-grades"

LANGUAGE_CODE = "ar"
PLATFORM_NAME = u"إدراك"
SITE_NAME = "www.edraak.org"
TIME_ZONE = "Asia/Amman"

PLATFORM_FACEBOOK_ACCOUNT = "https://www.facebook.com/edraakorg"
PLATFORM_TWITTER_ACCOUNT = "@edraak"

FEEDBACK_SUBMISSION_EMAIL = "info@edraak.or"
PAYMENT_SUPPORT_EMAIL = "info@edraak.org"
SERVER_EMAIL = "dev@qrf.org"
PRESS_EMAIL = "syacoub@qrf.org"
CONTACT_EMAIL = "info@edraak.org"
COLLABORATE_EMAIL = "info@edraak.org"
TECH_SUPPORT_EMAIL = "dev@qrf.org"
UNIVERSITY_EMAIL = "info@edraak.org"

WIKI_ENABLED = False


LANGUAGES = (
    ("ar", u"العربية"),
    ("en", "English")
)

REGISTRATION_EXTRA_FIELDS = {
    "city": "hidden",
    "country": "required",
    "gender": "required",
    "goals": "optional",
    "honor_code": "required",
    "level_of_education": "required",
    "mailing_address": "hidden",
    "year_of_birth": "required"
}


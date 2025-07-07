"""
Common Django settings for Open edX services.

This module defines configuration shared between the LMS and CMS (Studio)
environments. It centralizes common settings in one place and reduces duplication.

Service-specific settings should import from this module and override as needed.

Note: More settings will be added to this file as the effort to simplify
settings moves forward. See docs/decisions/0022-settings-simplification.rst for
more details on the effort to simplify settings across Open edX services.

To create section headers in this file, use the following function:

```python
def center_with_hashes(text: str, width: int = 76):
    print(f"{f' {text} ':#^{width}}")
```
"""
import os
from path import Path as path

from django.utils.translation import gettext_lazy as _

from openedx.core.lib.derived import Derived

from openedx.core.djangoapps.theming.helpers_dirs import (
    get_themes_unchecked,
    get_theme_base_dirs_from_settings
)

from openedx.core.constants import (  # pylint: disable=unused-import
    ASSET_KEY_PATTERN,
    COURSE_KEY_REGEX,
    COURSE_KEY_PATTERN,
    COURSE_ID_PATTERN,
    USAGE_KEY_PATTERN,
    USAGE_ID_PATTERN,
)

################ Shared Functions for Derived Configuration ################


def make_mako_template_dirs(settings):
    """
    Derives the final list of Mako template directories based on the provided settings.

    Args:
        settings: A Django settings module object.

    Returns:
        list: A list of Mako template directories, potentially updated with additional
        theme directories.
    """
    if settings.ENABLE_COMPREHENSIVE_THEMING:
        themes_dirs = get_theme_base_dirs_from_settings(settings.COMPREHENSIVE_THEME_DIRS)
        for theme in get_themes_unchecked(themes_dirs, settings.PROJECT_ROOT):
            if theme.themes_base_dir not in settings.MAKO_TEMPLATE_DIRS_BASE:
                settings.MAKO_TEMPLATE_DIRS_BASE.insert(0, theme.themes_base_dir)
    return settings.MAKO_TEMPLATE_DIRS_BASE


def _make_locale_paths(settings):
    """
    Constructs a list of paths to locale directories used for translation.

    Localization (l10n) strings (e.g. django.po) are found in these directories.

    Args:
        settings: A Django settings module object.

    Returns:
        list: A list of paths, `str` or `path.Path`, to locale directories.
    """
    locale_paths = list(settings.PREPEND_LOCALE_PATHS)
    locale_paths += [settings.REPO_ROOT + '/conf/locale']  # edx-platform/conf/locale/

    if settings.ENABLE_COMPREHENSIVE_THEMING:
        # Add locale paths to settings for comprehensive theming.
        for locale_path in settings.COMPREHENSIVE_THEME_LOCALE_PATHS:
            locale_paths += (path(locale_path), )
    return locale_paths

############################# Django Built-Ins #############################

USE_TZ = True

# User-uploaded content
MEDIA_ROOT = '/edx/var/edxapp/media/'
MEDIA_URL = '/media/'

# Dummy secret key for dev/test
SECRET_KEY = 'dev key'

STATICI18N_OUTPUT_DIR = "js/i18n"

# Sourced from http://www.localeplanet.com/icu/ and wikipedia
LANGUAGES = [
    ('en', 'English'),
    ('rtl', 'Right-to-Left Test Language'),
    ('eo', 'Dummy Language (Esperanto)'),  # Dummy languaged used for testing

    ('am', 'አማርኛ'),  # Amharic
    ('ar', 'العربية'),  # Arabic
    ('az', 'azərbaycanca'),  # Azerbaijani
    ('bg-bg', 'български (България)'),  # Bulgarian (Bulgaria)
    ('bn-bd', 'বাংলা (বাংলাদেশ)'),  # Bengali (Bangladesh)
    ('bn-in', 'বাংলা (ভারত)'),  # Bengali (India)
    ('bs', 'bosanski'),  # Bosnian
    ('ca', 'Català'),  # Catalan
    ('ca@valencia', 'Català (València)'),  # Catalan (Valencia)
    ('cs', 'Čeština'),  # Czech
    ('cy', 'Cymraeg'),  # Welsh
    ('da', 'dansk'),  # Danish
    ('de-de', 'Deutsch (Deutschland)'),  # German (Germany)
    ('el', 'Ελληνικά'),  # Greek
    ('en-uk', 'English (United Kingdom)'),  # English (United Kingdom)
    ('en@lolcat', 'LOLCAT English'),  # LOLCAT English
    ('en@pirate', 'Pirate English'),  # Pirate English
    ('es-419', 'Español (Latinoamérica)'),  # Spanish (Latin America)
    ('es-ar', 'Español (Argentina)'),  # Spanish (Argentina)
    ('es-ec', 'Español (Ecuador)'),  # Spanish (Ecuador)
    ('es-es', 'Español (España)'),  # Spanish (Spain)
    ('es-mx', 'Español (México)'),  # Spanish (Mexico)
    ('es-pe', 'Español (Perú)'),  # Spanish (Peru)
    ('et-ee', 'Eesti (Eesti)'),  # Estonian (Estonia)
    ('eu-es', 'euskara (Espainia)'),  # Basque (Spain)
    ('fa', 'فارسی'),  # Persian
    ('fa-ir', 'فارسی (ایران)'),  # Persian (Iran)
    ('fi-fi', 'Suomi (Suomi)'),  # Finnish (Finland)
    ('fil', 'Filipino'),  # Filipino
    ('fr', 'Français'),  # French
    ('gl', 'Galego'),  # Galician
    ('gu', 'ગુજરાતી'),  # Gujarati
    ('he', 'עברית'),  # Hebrew
    ('hi', 'हिन्दी'),  # Hindi
    ('hr', 'hrvatski'),  # Croatian
    ('hu', 'magyar'),  # Hungarian
    ('hy-am', 'Հայերեն (Հայաստան)'),  # Armenian (Armenia)
    ('id', 'Bahasa Indonesia'),  # Indonesian
    ('it-it', 'Italiano (Italia)'),  # Italian (Italy)
    ('ja-jp', '日本語 (日本)'),  # Japanese (Japan)
    ('kk-kz', 'қазақ тілі (Қазақстан)'),  # Kazakh (Kazakhstan)
    ('km-kh', 'ភាសាខ្មែរ (កម្ពុជា)'),  # Khmer (Cambodia)
    ('kn', 'ಕನ್ನಡ'),  # Kannada
    ('ko-kr', '한국어 (대한민국)'),  # Korean (Korea)
    ('lt-lt', 'Lietuvių (Lietuva)'),  # Lithuanian (Lithuania)
    ('ml', 'മലയാളം'),  # Malayalam
    ('mn', 'Монгол хэл'),  # Mongolian
    ('mr', 'मराठी'),  # Marathi
    ('ms', 'Bahasa Melayu'),  # Malay
    ('nb', 'Norsk bokmål'),  # Norwegian Bokmål
    ('ne', 'नेपाली'),  # Nepali
    ('nl-nl', 'Nederlands (Nederland)'),  # Dutch (Netherlands)
    ('or', 'ଓଡ଼ିଆ'),  # Oriya
    ('pl', 'Polski'),  # Polish
    ('pt-br', 'Português (Brasil)'),  # Portuguese (Brazil)
    ('pt-pt', 'Português (Portugal)'),  # Portuguese (Portugal)
    ('ro', 'română'),  # Romanian
    ('ru', 'Русский'),  # Russian
    ('si', 'සිංහල'),  # Sinhala
    ('sk', 'Slovenčina'),  # Slovak
    ('sl', 'Slovenščina'),  # Slovenian
    ('sq', 'shqip'),  # Albanian
    ('sr', 'Српски'),  # Serbian
    ('sv', 'svenska'),  # Swedish
    ('sw', 'Kiswahili'),  # Swahili
    ('ta', 'தமிழ்'),  # Tamil
    ('te', 'తెలుగు'),  # Telugu
    ('th', 'ไทย'),  # Thai
    ('tr-tr', 'Türkçe (Türkiye)'),  # Turkish (Turkey)
    ('uk', 'Українська'),  # Ukranian
    ('ur', 'اردو'),  # Urdu
    ('vi', 'Tiếng Việt'),  # Vietnamese
    ('uz', 'Ўзбек'),  # Uzbek
    ('zh-cn', '中文 (简体)'),  # Chinese (China)
    ('zh-hk', '中文 (香港)'),  # Chinese (Hong Kong)
    ('zh-tw', '中文 (台灣)'),  # Chinese (Taiwan)
]

# these languages display right to left
LANGUAGES_BIDI = ("he", "ar", "fa", "ur", "fa-ir", "rtl")

LANGUAGE_COOKIE_NAME = "openedx-language-preference"

LOCALE_PATHS = Derived(_make_locale_paths)

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "common.djangoapps.util.password_policy_validators.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 8
        }
    },
    {
        "NAME": "common.djangoapps.util.password_policy_validators.MaximumLengthValidator",
        "OPTIONS": {
            "max_length": 75
        }
    },
]

# See https://github.com/openedx/edx-django-sites-extensions for more info.
# Default site to use if site matching request headers does not exist.
SITE_ID = 1

################################# Language #################################

# Source:
# http://loc.gov/standards/iso639-2/ISO-639-2_utf-8.txt according to http://en.wikipedia.org/wiki/ISO_639-1
# Note that this is used as the set of choices to the `code` field of the `LanguageProficiency` model.
ALL_LANGUAGES = [
    ["aa", "Afar"],
    ["ab", "Abkhazian"],
    ["af", "Afrikaans"],
    ["ak", "Akan"],
    ["sq", "Albanian"],
    ["am", "Amharic"],
    ["ar", "Arabic"],
    ["an", "Aragonese"],
    ["hy", "Armenian"],
    ["as", "Assamese"],
    ["av", "Avaric"],
    ["ae", "Avestan"],
    ["ay", "Aymara"],
    ["az", "Azerbaijani"],
    ["ba", "Bashkir"],
    ["bm", "Bambara"],
    ["eu", "Basque"],
    ["be", "Belarusian"],
    ["bn", "Bengali"],
    ["bh", "Bihari languages"],
    ["bi", "Bislama"],
    ["bs", "Bosnian"],
    ["br", "Breton"],
    ["bg", "Bulgarian"],
    ["my", "Burmese"],
    ["ca", "Catalan"],
    ["ch", "Chamorro"],
    ["ce", "Chechen"],
    ["zh", "Chinese"],
    ["zh_HANS", "Simplified Chinese"],
    ["zh_HANT", "Traditional Chinese"],
    ["cu", "Church Slavic"],
    ["cv", "Chuvash"],
    ["kw", "Cornish"],
    ["co", "Corsican"],
    ["cr", "Cree"],
    ["cs", "Czech"],
    ["da", "Danish"],
    ["dv", "Divehi"],
    ["nl", "Dutch"],
    ["dz", "Dzongkha"],
    ["en", "English"],
    ["eo", "Esperanto"],
    ["et", "Estonian"],
    ["ee", "Ewe"],
    ["fo", "Faroese"],
    ["fj", "Fijian"],
    ["fi", "Finnish"],
    ["fr", "French"],
    ["fy", "Western Frisian"],
    ["ff", "Fulah"],
    ["ka", "Georgian"],
    ["de", "German"],
    ["gd", "Gaelic"],
    ["ga", "Irish"],
    ["gl", "Galician"],
    ["gv", "Manx"],
    ["el", "Greek"],
    ["gn", "Guarani"],
    ["gu", "Gujarati"],
    ["ht", "Haitian"],
    ["ha", "Hausa"],
    ["he", "Hebrew"],
    ["hz", "Herero"],
    ["hi", "Hindi"],
    ["ho", "Hiri Motu"],
    ["hr", "Croatian"],
    ["hu", "Hungarian"],
    ["ig", "Igbo"],
    ["is", "Icelandic"],
    ["io", "Ido"],
    ["ii", "Sichuan Yi"],
    ["iu", "Inuktitut"],
    ["ie", "Interlingue"],
    ["ia", "Interlingua"],
    ["id", "Indonesian"],
    ["ik", "Inupiaq"],
    ["it", "Italian"],
    ["jv", "Javanese"],
    ["ja", "Japanese"],
    ["kl", "Kalaallisut"],
    ["kn", "Kannada"],
    ["ks", "Kashmiri"],
    ["kr", "Kanuri"],
    ["kk", "Kazakh"],
    ["km", "Central Khmer"],
    ["ki", "Kikuyu"],
    ["rw", "Kinyarwanda"],
    ["ky", "Kirghiz"],
    ["kv", "Komi"],
    ["kg", "Kongo"],
    ["ko", "Korean"],
    ["kj", "Kuanyama"],
    ["ku", "Kurdish"],
    ["lo", "Lao"],
    ["la", "Latin"],
    ["lv", "Latvian"],
    ["li", "Limburgan"],
    ["ln", "Lingala"],
    ["lt", "Lithuanian"],
    ["lb", "Luxembourgish"],
    ["lu", "Luba-Katanga"],
    ["lg", "Ganda"],
    ["mk", "Macedonian"],
    ["mh", "Marshallese"],
    ["ml", "Malayalam"],
    ["mi", "Maori"],
    ["mr", "Marathi"],
    ["ms", "Malay"],
    ["mg", "Malagasy"],
    ["mt", "Maltese"],
    ["mn", "Mongolian"],
    ["na", "Nauru"],
    ["nv", "Navajo"],
    ["nr", "Ndebele, South"],
    ["nd", "Ndebele, North"],
    ["ng", "Ndonga"],
    ["ne", "Nepali"],
    ["nn", "Norwegian Nynorsk"],
    ["nb", "Bokmål, Norwegian"],
    ["no", "Norwegian"],
    ["ny", "Chichewa"],
    ["oc", "Occitan"],
    ["oj", "Ojibwa"],
    ["or", "Oriya"],
    ["om", "Oromo"],
    ["os", "Ossetian"],
    ["pa", "Panjabi"],
    ["fa", "Persian"],
    ["pi", "Pali"],
    ["pl", "Polish"],
    ["pt", "Portuguese"],
    ["ps", "Pushto"],
    ["qu", "Quechua"],
    ["rm", "Romansh"],
    ["ro", "Romanian"],
    ["rn", "Rundi"],
    ["ru", "Russian"],
    ["sg", "Sango"],
    ["sa", "Sanskrit"],
    ["si", "Sinhala"],
    ["sk", "Slovak"],
    ["sl", "Slovenian"],
    ["se", "Northern Sami"],
    ["sm", "Samoan"],
    ["sn", "Shona"],
    ["sd", "Sindhi"],
    ["so", "Somali"],
    ["st", "Sotho, Southern"],
    ["es", "Spanish"],
    ["sc", "Sardinian"],
    ["sr", "Serbian"],
    ["ss", "Swati"],
    ["su", "Sundanese"],
    ["sw", "Swahili"],
    ["sv", "Swedish"],
    ["ty", "Tahitian"],
    ["ta", "Tamil"],
    ["tt", "Tatar"],
    ["te", "Telugu"],
    ["tg", "Tajik"],
    ["tl", "Tagalog"],
    ["th", "Thai"],
    ["bo", "Tibetan"],
    ["ti", "Tigrinya"],
    ["to", "Tonga (Tonga Islands)"],
    ["tn", "Tswana"],
    ["ts", "Tsonga"],
    ["tk", "Turkmen"],
    ["tr", "Turkish"],
    ["tw", "Twi"],
    ["ug", "Uighur"],
    ["uk", "Ukrainian"],
    ["ur", "Urdu"],
    ["uz", "Uzbek"],
    ["ve", "Venda"],
    ["vi", "Vietnamese"],
    ["vo", "Volapük"],
    ["cy", "Welsh"],
    ["wa", "Walloon"],
    ["wo", "Wolof"],
    ["xh", "Xhosa"],
    ["yi", "Yiddish"],
    ["yo", "Yoruba"],
    ["za", "Zhuang"],
    ["zu", "Zulu"]
]

LANGUAGE_DICT = dict(LANGUAGES)

########################## Django Rest Framework ###########################

REST_FRAMEWORK = {
    # These default classes add observability around endpoints using defaults, and should
    # not be used anywhere else.
    # Notes on Order:
    # 1. `JwtAuthentication` does not check `is_active`, so email validation does not affect it. However,
    #    `SessionAuthentication` does. These work differently, and order changes in what way, which really stinks. See
    #    https://github.com/openedx/public-engineering/issues/165 for details.
    # 2. `JwtAuthentication` may also update the database based on contents. Since the LMS creates these JWTs, this
    #    shouldn't have any affect at this time. But it could, when and if another service started creating the JWTs.
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'openedx.core.djangolib.default_auth_classes.DefaultJwtAuthentication',
        'openedx.core.djangolib.default_auth_classes.DefaultSessionAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'edx_rest_framework_extensions.paginators.DefaultPagination',
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'EXCEPTION_HANDLER': 'openedx.core.lib.request_utils.ignored_error_exception_handler',
    'PAGE_SIZE': 10,
    'URL_FORMAT_OVERRIDE': None,
    'DEFAULT_THROTTLE_RATES': {
        'user': '60/minute',
        'service_user': '800/minute',
        'registration_validation': '30/minute',
        'high_service_user': '2000/minute',
    },
}

################################ Heartbeat #################################

# Checks run in normal mode by the heartbeat djangoapp
HEARTBEAT_CHECKS = [
    'openedx.core.djangoapps.heartbeat.default_checks.check_modulestore',
    'openedx.core.djangoapps.heartbeat.default_checks.check_database',
]

# Other checks to run by default in "extended"/heavy mode
HEARTBEAT_EXTENDED_CHECKS = (
    'openedx.core.djangoapps.heartbeat.default_checks.check_celery',
)

HEARTBEAT_CELERY_TIMEOUT = 5

############################ RedirectMiddleware ############################

# Setting this to None causes Redirect data to never expire
# The cache is cleared when Redirect models are saved/deleted
REDIRECT_CACHE_TIMEOUT = None  # The length of time we cache Redirect model data
REDIRECT_CACHE_KEY_PREFIX = 'redirects'

########################### Django Debug Toolbar ###########################

# We don't enable Django Debug Toolbar universally, but whenever we do, we want
# to avoid patching settings.  Patched settings can cause circular import
# problems: https://django-debug-toolbar.readthedocs.org/en/1.0/installation.html#explicit-setup

DEBUG_TOOLBAR_PATCH_SETTINGS = False

################################### JWT ####################################

JWT_AUTH = {
    'JWT_VERIFY_EXPIRATION': True,

    'JWT_PAYLOAD_GET_USERNAME_HANDLER': lambda d: d.get('username'),
    'JWT_LEEWAY': 1,
    'JWT_DECODE_HANDLER': 'edx_rest_framework_extensions.auth.jwt.decoder.jwt_decode_handler',

    'JWT_AUTH_COOKIE': 'edx-jwt-cookie',

    # Number of seconds before JWTs expire
    'JWT_EXPIRATION': 30,
    'JWT_IN_COOKIE_EXPIRATION': 60 * 60,

    'JWT_LOGIN_CLIENT_ID': 'login-service-client-id',
    'JWT_LOGIN_SERVICE_USERNAME': 'login_service_user',

    'JWT_SUPPORTED_VERSION': '1.2.0',

    'JWT_ALGORITHM': 'HS256',
    'JWT_SECRET_KEY': SECRET_KEY,

    'JWT_SIGNING_ALGORITHM': 'RS512',
    'JWT_PRIVATE_SIGNING_JWK': None,
    'JWT_PUBLIC_SIGNING_JWK_SET': None,

    'JWT_ISSUER': 'http://127.0.0.1:8000/oauth2',
    'JWT_AUDIENCE': 'change-me',
    'JWT_ISSUERS': [
        {
            'ISSUER': 'http://127.0.0.1:8000/oauth2',
            'AUDIENCE': 'change-me',
            'SECRET_KEY': SECRET_KEY
        }
    ],
    'JWT_AUTH_COOKIE_HEADER_PAYLOAD': 'edx-jwt-cookie-header-payload',
    'JWT_AUTH_COOKIE_SIGNATURE': 'edx-jwt-cookie-signature',
    'JWT_AUTH_HEADER_PREFIX': 'JWT',
}

############################ Parental Controls #############################

# .. setting_name: PARENTAL_CONSENT_AGE_LIMIT
# .. setting_default: 13
# .. setting_description: The age at which a learner no longer requires parental consent,
#   or ``None`` if parental consent is never required.
PARENTAL_CONSENT_AGE_LIMIT = 13

############################### Registration ###############################

# .. setting_name: REGISTRATION_EMAIL_PATTERNS_ALLOWED
# .. setting_default: None
# .. setting_description: Optional setting to restrict registration / account creation
#   to only emails that match a regex in this list. Set to ``None`` to allow any email (default).
REGISTRATION_EMAIL_PATTERNS_ALLOWED = None

######################### Course Enrollment Modes ##########################

# The min_price key refers to the minimum price allowed for an instance
# of a particular type of course enrollment mode. This is not to be confused
# with the min_price field of the CourseMode model, which refers to the actual
# price of the CourseMode.
COURSE_ENROLLMENT_MODES = {
    "audit": {
        "id": 1,
        "slug": "audit",
        "display_name": _("Audit"),
        "min_price": 0,
    },
    "verified": {
        "id": 2,
        "slug": "verified",
        "display_name": _("Verified"),
        "min_price": 1,
    },
    "professional": {
        "id": 3,
        "slug": "professional",
        "display_name": _("Professional"),
        "min_price": 1,
    },
    "no-id-professional": {
        "id": 4,
        "slug": "no-id-professional",
        "display_name": _("No-Id-Professional"),
        "min_price": 0,
    },
    "credit": {
        "id": 5,
        "slug": "credit",
        "display_name": _("Credit"),
        "min_price": 0,
    },
    "honor": {
        "id": 6,
        "slug": "honor",
        "display_name": _("Honor"),
        "min_price": 0,
    },
    "masters": {
        "id": 7,
        "slug": "masters",
        "display_name": _("Master's"),
        "min_price": 0,
    },
    "executive-education": {
        "id": 8,
        "slug": "executive-educations",
        "display_name": _("Executive Education"),
        "min_price": 1
    },
    "unpaid-executive-education": {
        "id": 9,
        "slug": "unpaid-executive-education",
        "display_name": _("Unpaid Executive Education"),
        "min_price": 0
    },
    "paid-executive-education": {
        "id": 10,
        "slug": "paid-executive-education",
        "display_name": _("Paid Executive Education"),
        "min_price": 1
    },
    "unpaid-bootcamp": {
        "id": 11,
        "slug": "unpaid-bootcamp",
        "display_name": _("Unpaid Bootcamp"),
        "min_price": 0
    },
    "paid-bootcamp": {
        "id": 12,
        "slug": "paid-bootcamp",
        "display_name": _("Paid Bootcamp"),
        "min_price": 1
    },
}

CONTENT_TYPE_GATE_GROUP_IDS = {
    'limited_access': 1,
    'full_access': 2,
}

########################## Enterprise Api Client ###########################

ENTERPRISE_CATALOG_INTERNAL_ROOT_URL = 'http://enterprise.catalog.app:18160'

ENTERPRISE_BACKEND_SERVICE_EDX_OAUTH2_KEY = "enterprise-backend-service-key"
ENTERPRISE_BACKEND_SERVICE_EDX_OAUTH2_SECRET = "enterprise-backend-service-secret"
ENTERPRISE_BACKEND_SERVICE_EDX_OAUTH2_PROVIDER_URL = "http://127.0.0.1:8000/oauth2"


############################### ModuleStore ################################

ASSET_IGNORE_REGEX = r"(^\._.*$)|(^\.DS_Store$)|(^.*~$)"

########################### Django OAuth Toolkit ###########################

# This is required for the migrations in oauth_dispatch.models
# otherwise it fails saying this attribute is not present in Settings

# Although Studio does not enable OAuth2 Provider capability, the new approach
# to generating test databases will discover and try to create all tables
# and this setting needs to be present

OAUTH2_PROVIDER_APPLICATION_MODEL = 'oauth2_provider.Application'

############################## Profile Image ###############################

# The following PROFILE_IMAGE_* settings are included as common settings as
# they are indirectly accessed through the email opt-in API, which is
# technically accessible through the CMS via legacy URLs.

# WARNING: Certain django storage backends do not support atomic
# file overwrites (including the default, OverwriteStorage) - instead
# there are separate calls to delete and then write a new file in the
# storage backend.  This introduces the risk of a race condition
# occurring when a user uploads a new profile image to replace an
# earlier one (the file will temporarily be deleted).
PROFILE_IMAGE_BACKEND = {
    'class': 'openedx.core.storage.OverwriteStorage',
    'options': {
        'location': os.path.join(MEDIA_ROOT, 'profile-images/'),
        'base_url': os.path.join(MEDIA_URL, 'profile-images/'),
    },
}
PROFILE_IMAGE_DEFAULT_FILENAME = 'images/profiles/default'
PROFILE_IMAGE_DEFAULT_FILE_EXTENSION = 'png'
# This key is used in generating unguessable URLs to users'
# profile images. Once it has been set, changing it will make the
# platform unaware of current image URLs.
PROFILE_IMAGE_HASH_SEED = 'placeholder_secret_key'
PROFILE_IMAGE_MAX_BYTES = 1024 * 1024
PROFILE_IMAGE_MIN_BYTES = 100
PROFILE_IMAGE_SIZES_MAP = {
    'full': 500,
    'large': 120,
    'medium': 50,
    'small': 30
}

######################## Built-in Blocks Extraction ########################

# The following Django settings flags have been introduced temporarily to facilitate
# the rollout of the extracted built-in Blocks. Flags will use to toggle between
# the old and new block quickly without putting course content or user state at risk.
#
# Ticket: https://github.com/openedx/edx-platform/issues/35308

# .. toggle_name: USE_EXTRACTED_WORD_CLOUD_BLOCK
# .. toggle_default: False
# .. toggle_implementation: DjangoSetting
# .. toggle_description: Enables the use of the extracted Word Cloud XBlock, which has been shifted to the 'openedx/xblocks-contrib' repo.
# .. toggle_use_cases: temporary
# .. toggle_warning: Not production-ready until https://github.com/openedx/edx-platform/issues/34840 is done.
# .. toggle_creation_date: 2024-11-10
# .. toggle_target_removal_date: 2025-06-01
USE_EXTRACTED_WORD_CLOUD_BLOCK = False

# .. toggle_name: USE_EXTRACTED_ANNOTATABLE_BLOCK
# .. toggle_default: False
# .. toggle_implementation: DjangoSetting
# .. toggle_description: Enables the use of the extracted annotatable XBlock, which has been shifted to the 'openedx/xblocks-contrib' repo.
# .. toggle_use_cases: temporary
# .. toggle_warning: Not production-ready until https://github.com/openedx/edx-platform/issues/34841 is done.
# .. toggle_creation_date: 2024-11-10
# .. toggle_target_removal_date: 2025-06-01
USE_EXTRACTED_ANNOTATABLE_BLOCK = False

# .. toggle_name: USE_EXTRACTED_POLL_QUESTION_BLOCK
# .. toggle_default: False
# .. toggle_implementation: DjangoSetting
# .. toggle_description: Enables the use of the extracted poll question XBlock, which has been shifted to the 'openedx/xblocks-contrib' repo.
# .. toggle_use_cases: temporary
# .. toggle_warning: Not production-ready until https://github.com/openedx/edx-platform/issues/34839 is done.
# .. toggle_creation_date: 2024-11-10
# .. toggle_target_removal_date: 2025-06-01
USE_EXTRACTED_POLL_QUESTION_BLOCK = False

# .. toggle_name: USE_EXTRACTED_LTI_BLOCK
# .. toggle_default: False
# .. toggle_implementation: DjangoSetting
# .. toggle_description: Enables the use of the extracted LTI XBlock, which has been shifted to the 'openedx/xblocks-contrib' repo.
# .. toggle_use_cases: temporary
# .. toggle_warning: Not production-ready until relevant subtask https://github.com/openedx/edx-platform/issues/34827 is done.
# .. toggle_creation_date: 2024-11-10
# .. toggle_target_removal_date: 2025-06-01
USE_EXTRACTED_LTI_BLOCK = False

# .. toggle_name: USE_EXTRACTED_HTML_BLOCK
# .. toggle_default: False
# .. toggle_implementation: DjangoSetting
# .. toggle_description: Enables the use of the extracted HTML XBlock, which has been shifted to the 'openedx/xblocks-contrib' repo.
# .. toggle_use_cases: temporary
# .. toggle_warning: Not production-ready until relevant subtask https://github.com/openedx/edx-platform/issues/34827 is done.
# .. toggle_creation_date: 2024-11-10
# .. toggle_target_removal_date: 2025-06-01
USE_EXTRACTED_HTML_BLOCK = False

# .. toggle_name: USE_EXTRACTED_DISCUSSION_BLOCK
# .. toggle_default: False
# .. toggle_implementation: DjangoSetting
# .. toggle_description: Enables the use of the extracted Discussion XBlock, which has been shifted to the 'openedx/xblocks-contrib' repo.
# .. toggle_use_cases: temporary
# .. toggle_warning: Not production-ready until relevant subtask https://github.com/openedx/edx-platform/issues/34827 is done.
# .. toggle_creation_date: 2024-11-10
# .. toggle_target_removal_date: 2025-06-01
USE_EXTRACTED_DISCUSSION_BLOCK = False

# .. toggle_name: USE_EXTRACTED_PROBLEM_BLOCK
# .. toggle_default: False
# .. toggle_implementation: DjangoSetting
# .. toggle_description: Enables the use of the extracted Problem XBlock, which has been shifted to the 'openedx/xblocks-contrib' repo.
# .. toggle_use_cases: temporary
# .. toggle_warning: Not production-ready until relevant subtask https://github.com/openedx/edx-platform/issues/34827 is done.
# .. toggle_creation_date: 2024-11-10
# .. toggle_target_removal_date: 2025-06-01
USE_EXTRACTED_PROBLEM_BLOCK = False

# .. toggle_name: USE_EXTRACTED_VIDEO_BLOCK
# .. toggle_default: False
# .. toggle_implementation: DjangoSetting
# .. toggle_description: Enables the use of the extracted Video XBlock, which has been shifted to the 'openedx/xblocks-contrib' repo.
# .. toggle_use_cases: temporary
# .. toggle_warning: Not production-ready until relevant subtask https://github.com/openedx/edx-platform/issues/34827 is done.
# .. toggle_creation_date: 2024-11-10
# .. toggle_target_removal_date: 2025-06-01
USE_EXTRACTED_VIDEO_BLOCK = False

############################## Miscellaneous ###############################

COURSE_MODE_DEFAULTS = {
    'android_sku': None,
    'bulk_sku': None,
    'currency': 'usd',
    'description': None,
    'expiration_datetime': None,
    'ios_sku': None,
    'min_price': 0,
    'name': _('Audit'),
    'sku': None,
    'slug': 'audit',
    'suggested_prices': '',
}

DEFAULT_COURSE_ABOUT_IMAGE_URL = 'images/pencils.jpg'

DISABLE_ACCOUNT_ACTIVATION_REQUIREMENT_SWITCH = "verify_student_disable_account_activation_requirement"

# If this is true, random scores will be generated for the purpose of debugging the profile graphs
GENERATE_PROFILE_SCORES = False

# The space is required for space-dependent languages like Arabic and Farsi.
# However, backward compatibility with Ficus older releases is still maintained (space is still not valid)
# in the AccountCreationForm and the user_api through the ENABLE_UNICODE_USERNAME feature flag.
USERNAME_REGEX_PARTIAL = r'[\w .@_+-]+'
USERNAME_PATTERN = fr'(?P<username>{USERNAME_REGEX_PARTIAL})'

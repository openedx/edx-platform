ASKBOT_ENABLED = True

DEFAULT_FROM_EMAIL = 'pmitros@csail.mit.edu'

WIKI_REQUIRE_LOGIN_EDIT = True
WIKI_REQUIRE_LOGIN_VIEW = True

HTTPS = 'on'

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Piotr Mitros', 'pmitros@csail.mit.edu'),
)

MANAGERS = ADMINS

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# URL prefix for admin static files -- CSS, JavaScript and images.
# Make sure to use a trailing slash.
# Examples: "http://foo.com/static/admin/", "/static/admin/".
ADMIN_MEDIA_PREFIX = '/static/admin/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'djangomako.middleware.MakoMiddleware',
    #'debug_toolbar.middleware.DebugToolbarMiddleware',
)

ROOT_URLCONF = 'mitx.urls'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'courseware',
    'auth',
    'django.contrib.humanize',
    'static_template_view',
    'textbook',
    'staticbook',
    'simplewiki',
    'track',
    # Uncomment the next line to enable the admin:
    # 'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
)

#EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

TRACK_DIR = None

# Django settings for mitx project.
execfile("../settings.py")

if ASKBOT_ENABLED:
   import sys
   sys.path.append(ASKBOT_DIR)
   import os
   import askbot
   import site
   site.addsitedir(os.path.join(os.path.dirname(askbot.__file__), 'deps'))
   TEMPLATE_LOADERS = TEMPLATE_LOADERS + ('askbot.skins.loaders.filesystem_load_template_source',)

   MIDDLEWARE_CLASSES = MIDDLEWARE_CLASSES + (
	   'askbot.middleware.anon_user.ConnectToSessionMessagesMiddleware',
	   'askbot.middleware.pagesize.QuestionsPageSizeMiddleware',
	   'askbot.middleware.cancel.CancelActionMiddleware',
	   'django.middleware.transaction.TransactionMiddleware',
	   'askbot.middleware.view_log.ViewLogMiddleware',
	   'askbot.middleware.spaceless.SpacelessMiddleware',
	   'askbot.middleware.forum_mode.ForumModeMiddleware',
	   )

   FILE_UPLOAD_TEMP_DIR = os.path.join(
	   os.path.dirname(__file__),
	   'tmp'
	   ).replace('\\','/')
   FILE_UPLOAD_HANDLERS = (
	   'django.core.files.uploadhandler.MemoryFileUploadHandler',
	   'django.core.files.uploadhandler.TemporaryFileUploadHandler',
	   )
   ASKBOT_ALLOWED_UPLOAD_FILE_TYPES = ('.jpg', '.jpeg', '.gif', '.bmp', '.png', '.tiff')
   ASKBOT_MAX_UPLOAD_FILE_SIZE = 1024 * 1024 #result in bytes
   ASKBOT_FILE_UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'askbot', 'upfiles')
   DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
   
   PROJECT_ROOT = os.path.dirname(__file__)
   
   TEMPLATE_CONTEXT_PROCESSORS = (
	   'django.core.context_processors.request',
	   'askbot.context.application_settings',
	   #'django.core.context_processors.i18n',
	   'askbot.user_messages.context_processors.user_messages',#must be before auth
	   'django.core.context_processors.auth', #this is required for admin
	   'django.core.context_processors.csrf', #necessary for csrf protection
	   )
   
   INSTALLED_APPS = INSTALLED_APPS + (
	   'django.contrib.sitemaps',
	   'django.contrib.admin',
	   'south',
	   'askbot.deps.livesettings',
	   'askbot',
	   'keyedcache',
	   'robots',
	   'django_countries',
	   'djcelery',
	   'djkombu',
	   'followit',
	   )
   
   CACHE_MIDDLEWARE_ANONYMOUS_ONLY = True
   ASKBOT_URL = 'discussion/'
   LOGIN_REDIRECT_URL = '/'
   LOGIN_URL = '/'
   
   ASKBOT_UPLOADED_FILES_URL = '%s%s' % (ASKBOT_URL, 'upfiles/')
   ALLOW_UNICODE_SLUGS = False
   ASKBOT_USE_STACKEXCHANGE_URLS = False #mimic url scheme of stackexchange
   ASKBOT_CSS_DEVEL = True
   
   #Celery Settings
   BROKER_TRANSPORT = "djkombu.transport.DatabaseTransport"
   CELERY_ALWAYS_EAGER = True
   
   import djcelery
   djcelery.setup_loader()

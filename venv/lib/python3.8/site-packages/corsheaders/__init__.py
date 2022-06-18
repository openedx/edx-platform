import django

if django.VERSION < (3, 2):
    default_app_config = "corsheaders.apps.CorsHeadersAppConfig"

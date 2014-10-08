from django.views.i18n import set_language as django_set_language
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def set_language(request):
    return django_set_language(request)
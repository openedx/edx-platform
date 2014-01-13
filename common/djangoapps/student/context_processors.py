from django.conf import settings
from .microsites import get_microsite_config


def microsite_processor(request):
    # these will be automatically injected into every template, under the
    # name `django_context`
    return {
        "microsite": get_microsite_config(request)
    }

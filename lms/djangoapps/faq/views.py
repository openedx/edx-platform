from django.utils.safestring import mark_safe
from edxmako.shortcuts import render_to_response

from lms.djangoapps.faq.models import Faq


def get_faq(request):
    """
    Display the Dynamic FAQ Page
    """

    faq_page = Faq.objects.filter(is_active=True).last()
    context = {
        'title': faq_page.title if faq_page else 'FAQ',
        'body': mark_safe(faq_page.content) if faq_page else '** Please add content for FAQ page',
    }

    return render_to_response("faq/custom_faq.html", context)

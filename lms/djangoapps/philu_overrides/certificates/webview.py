from openedx.features.student_certificates.helpers import get_philu_certificate_social_context


def override_update_social_context(request, context, course, user, user_certificate, platform_name):
    border = request.GET.get('border', None)
    if border and border == 'hide':
        context['border_class'] = 'certificate-border-hide'
    else:
        context['border_class'] = ''

    context['social_sharing_urls'] = get_philu_certificate_social_context(course, user_certificate)

from django.http import HttpResponseRedirect
from django.contrib.auth.models import User
from django.core.exceptions import MultipleObjectsReturned
from django.urls import reverse
from django.conf.urls import url
from django.conf import settings
from django.template.response import TemplateResponse
from django.utils.html import format_html
from hijack_admin.admin import HijackUserAdminMixin
from ratelimitbackend import admin
from student.admin import UserAdmin
from organizations.models import Organization
from tahoe_sites.api import get_organization_for_user

from openedx.core.djangolib.markup import HTML, Text
from openedx.core.djangoapps.appsembler.sites.models import AlternativeDomain

from openedx.core.djangoapps.appsembler.sites.forms import MakeAMCAdminForm
from openedx.core.djangoapps.appsembler.sites.utils import (
    get_amc_tokens,
    make_amc_admin,
)


class TahoeUserAdmin(UserAdmin, HijackUserAdminMixin):
    list_display = UserAdmin.list_display + (
        'hijack_field',
        'amc_actions',
    )

    def get_urls(self):
        return [
            url(
                r'^(?P<user_id>\d+)/make-amc-admin$',
                self.admin_site.admin_view(self.process_make_amc_admin),
                name='make-amc-admin',
            ),
        ] + super(UserAdmin, self).get_urls()

    def amc_actions(self, obj):
        return format_html(
            '<a class="button" href="{href}">AMC Admin Form</a> ',
            href=reverse('admin:make-amc-admin', args=[obj.id])
        )

    def process_make_amc_admin(self, request, user_id, *args, **kwargs):
        user = self.get_object(request, user_id)

        try:
            current_org = get_organization_for_user(user)
            current_org_name = current_org.name
        except (Organization.DoesNotExist, MultipleObjectsReturned):
            current_org_name = ''

        form = MakeAMCAdminForm({'organization_name': current_org_name})

        if request.method == 'POST':
            form = MakeAMCAdminForm(request.POST)
            if form.is_valid():
                make_amc_admin(user, form.cleaned_data['organization_name'])
                self.message_user(request, HTML('Successfully made "{user}" an AMC admin for "{org}"').format(
                    user=Text(user.username),
                    org=Text(form.cleaned_data['organization_name']),
                ))
                return HttpResponseRedirect(reverse('admin:make-amc-admin', args=[user.id]))

        context = self.admin_site.each_context(request)
        context.update({
            'opts': self.model._meta,  # pylint: disable=protected-access
            'form': form,
            'amc_user': user,
            'amc_app_url': settings.AMC_APP_URL,
            'title': 'Make AMC Admin',
            'tokens': get_amc_tokens(user),
        })
        return TemplateResponse(
            request,
            'admin/user/make_amc_admin_action.html',
            context,
        )


class AlternativeDomainAdmin(admin.ModelAdmin):
    list_display = (
        'domain',
        'site'
    )


admin.site.unregister(User)
admin.site.register(User, TahoeUserAdmin)
admin.site.register(AlternativeDomain, AlternativeDomainAdmin)

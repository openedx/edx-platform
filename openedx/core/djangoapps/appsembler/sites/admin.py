from django.http import HttpResponseRedirect
from django.contrib.auth.models import User
from django.core.exceptions import MultipleObjectsReturned
from django.core.urlresolvers import reverse
from django.conf.urls import url
from django.template.response import TemplateResponse
from hijack_admin.admin import HijackUserAdminMixin
from ratelimitbackend import admin
from student.admin import UserAdmin
from openedx.core.djangolib.markup import HTML, Text
from .models import AlternativeDomain
from organizations.models import Organization



from openedx.core.djangoapps.appsembler.sites.models import MakeAMCAdminForm
from openedx.core.djangoapps.appsembler.sites.utils import make_amc_admin, get_single_user_organization


class TahoeUserAdmin(UserAdmin, HijackUserAdminMixin):
    list_display = UserAdmin.list_display + (
        'hijack_field',
        'make_amc_admin_action',
    )

    def get_urls(self):
        return [
            url(
                r'^(?P<user_id>\d+)/make-amc-admin$',
                self.admin_site.admin_view(self.process_make_amc_admin),
                name='make-amc-admin',
            ),
        ] + super(UserAdmin, self).get_urls()

    def make_amc_admin_action(self, obj):
        return HTML('<a class="button" href="{href}">Make AMC Admin...</a> ').format(
            href=Text(reverse('admin:make-amc-admin', args=[obj.id])),
        )
    make_amc_admin_action.short_description = 'AMC Actions'
    make_amc_admin_action.allow_tags = True

    def process_make_amc_admin(self, request, user_id, *args, **kwargs):
        user = self.get_object(request, user_id)
        form = MakeAMCAdminForm()

        try:
            current_org = get_single_user_organization(user)
            current_org_name = current_org.name
        except (Organization.DoesNotExist, MultipleObjectsReturned):
            current_org_name = ''

        if request.method == 'POST':
            initial = {'organization_name': current_org_name}
            initial.update(request.POST)
            form = MakeAMCAdminForm(initial)
            if form.is_valid():
                make_amc_admin(user, form.cleaned_data['organization_name'])
                self.message_user(request, HTML('Successfully made "{user}" an AMC admin for "{org}"').format(
                    user=Text(user.username),
                    org=Text(form.cleaned_data['organization_name']),
                ))
                return HttpResponseRedirect(reverse('admin:auth_user_change', args=[user.pk]))

        context = self.admin_site.each_context(request)
        context['opts'] = self.model._meta  # pylint: disable=protected-access
        context['form'] = form
        context['user'] = user
        context['title'] = 'Make AMC Admin'
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

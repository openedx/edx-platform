from django.http import HttpResponseRedirect
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.conf.urls import url
from django.template.response import TemplateResponse
from hijack_admin.admin import HijackUserAdminMixin
from ratelimitbackend import admin
from student.admin import UserAdmin
from openedx.core.djangolib.markup import HTML, Text
from .models import AlternativeDomain


from openedx.core.djangoapps.appsembler.sites.models import MakeAMCAdminForm


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

        if request.method != 'POST':
            form = MakeAMCAdminForm()
        else:
            form = MakeAMCAdminForm(request.POST)
            if form.is_valid():
                form.save(user, request.user)
                self.message_user(request, 'Success')
                url = reverse(
                    'admin:auth_user_change',
                    args=[user.pk],
                )
                return HttpResponseRedirect(url)
        context = self.admin_site.each_context(request)
        context['opts'] = self.model._meta
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

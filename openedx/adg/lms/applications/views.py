"""
All views for applications app
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic.edit import FormView

from openedx.adg.lms.applications.forms import ContactInformationForm
from openedx.adg.lms.utils.date_utils import day_choices, month_choices, year_choices


class ContactInformationView(LoginRequiredMixin, FormView):
    """
    View for the contact information of user application
    """

    template_name = 'adg/lms/applications/contact_info.html'
    form_class = ContactInformationForm
    login_url = '/register'
    success_url = reverse_lazy('application_experience')

    def get_context_data(self, **kwargs):
        context = super(ContactInformationView, self).get_context_data(**kwargs)
        context.update({
            'name': self.request.user.profile.name,
            'email': self.request.user.email,
            'city': self.request.user.profile.city,
            'saudi_national': self.request.user.extended_profile.saudi_national,
            'organization': self.request.user.extended_profile.company,
            'day_choices': day_choices(),
            'month_choices': month_choices(),
            'year_choices': year_choices(),
        })
        return context

    def form_valid(self, form):
        form.save(request=self.request)
        if form.cleaned_data.get('resume'):
            return HttpResponseRedirect(reverse_lazy('application_cover_letter'))
        return super(ContactInformationView, self).form_valid(form)

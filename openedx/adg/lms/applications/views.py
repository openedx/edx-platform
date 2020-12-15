"""
All views for applications app
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic.edit import FormView

from openedx.adg.lms.applications.forms import ContactInformationForm


class ContactInformationView(LoginRequiredMixin, FormView):
    """
    View for the contact information of user application
    """

    template_name = 'adg/lms/applications/contact_info.html'
    form_class = ContactInformationForm
    login_url = '/register'
    success_url = reverse_lazy('application_experience')

    def form_valid(self, form):
        form.save(request=self.request)
        if form.cleaned_data.get('resume'):
            return HttpResponseRedirect(reverse_lazy('application_cover_letter'))
        return super(ContactInformationView, self).form_valid(form)

    def get_initial(self):
        """
        Returns the initial data to use for forms on this view.
        """
        user = self.request.user
        initial = super().get_initial()
        initial['name'] = user.profile.name
        initial['email'] = user.email
        initial['city'] = user.profile.city
        initial['saudi_national'] = user.extended_profile.saudi_national
        initial['organization'] = user.extended_profile.company
        return initial

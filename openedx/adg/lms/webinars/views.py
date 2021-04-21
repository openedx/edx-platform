"""
All views for webinars app
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseServerError
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views import View
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic.detail import DetailView, SingleObjectMixin

from .helpers import send_webinar_registration_email
from .models import Webinar, WebinarRegistration


class WebinarDetailView(DetailView):
    """
    A view to get description about a specific webinar.
    """

    model = Webinar
    template_name = 'adg/lms/webinar/description_page.html'


@method_decorator(ensure_csrf_cookie, name='dispatch')
class WebinarRegistrationView(LoginRequiredMixin, SingleObjectMixin, View):
    """
    A view to register user in a webinar event or cancel already registered user in a webinar.
    """

    model = Webinar

    def post(self, request, pk, action):
        """
        Register in a webinar or cancel registration

        Args:
            request (HttpRequest): HTTP request
            pk (int): Webinar id, the primary key of model
            action (str): Actions to perform on event i.e. `register` or `cancel`

        Returns:
            HttpResponse: On success redirect to webinar page otherwise through HTTP error code as per nature
            of error i.e. 404 or 500
        """
        self.object = self.get_object()  # pylint: disable=attribute-defined-outside-init
        is_registering = action == 'register'
        user = request.user

        if is_registering and self.object.status == Webinar.CANCELLED:
            return HttpResponseServerError(_('You cannot register cancelled event'))

        registered_webinar_for_user = WebinarRegistration.objects.filter(
            webinar=self.object, user=user, is_registered=is_registering
        ).first()

        if not registered_webinar_for_user:
            WebinarRegistration.objects.update_or_create(
                webinar=self.object, user=user, defaults={'is_registered': is_registering}
            )
            # pylint: disable=expression-not-assigned
            send_webinar_registration_email(self.object, user.email) if is_registering else None

        return redirect(reverse('webinar_event', kwargs={'pk': pk}))

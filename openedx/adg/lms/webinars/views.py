"""
All views for webinars app
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseServerError
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views import View
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic.detail import SingleObjectMixin

from .helpers import cancel_all_reminders, schedule_webinar_reminders, send_webinar_registration_email
from .models import Webinar, WebinarRegistration


def webinar_description_page_view(request, pk):
    # TODO This is a temp view and will be properly functional in LP-2623
    return render(request, 'adg/lms/webinar/description_page.html', context={'pk': pk})


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
            registration, created = WebinarRegistration.objects.update_or_create(
                webinar=self.object, user=user, defaults={'is_registered': is_registering}
            )

            if is_registering:
                send_webinar_registration_email(self.object, user.email)
                if not registration.is_team_member_registration:
                    schedule_webinar_reminders([user.email], self.object.to_dict())

            elif not created and not registration.is_team_member_registration:
                cancel_all_reminders([registration])

        return redirect(reverse('webinar_event', kwargs={'pk': pk}))

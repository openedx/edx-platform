# Custom code by KN 
from django.contrib.sessions.models import Session
from openedx.core.djangoapps.user_authn.models import LoggedInUser as LIU

class ConcurrentLoginMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and request.session.session_key:
            session_key = request.session.session_key
            try:
                logged_in_user = LIU.objects.get(user=request.user)
                if logged_in_user.session_key != session_key:
                    # Delete old session
                    Session.objects.filter(session_key=logged_in_user.session_key).delete()
                    logged_in_user.session_key = session_key
                    logged_in_user.save()
            except LIU.DoesNotExist:
                # No record yet, create new session
                LIU.objects.create(user=request.user, session_key=session_key)

        response = self.get_response(request)
        return response

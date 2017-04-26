from django.http import Http404, HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from .models import TokenStorage


class ReceiveTokenView(View):
    """
    Receives a secret token from the remote server and save it to DB.
    This will allow edx-platform to exchange data with a remote server.
    """

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(ReceiveTokenView, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Receive generated token from the remote server and save it to DB.
        
        `secret_token` is uuid.UUID object converted to string.
        
        Return http status code based on success of the token's save operation.
        """

        try:
            received_data = self.request.POST
            secret_token = str(received_data.get('secret_token'))
            TokenStorage.objects.update_or_create(
                pk=1, defaults={"secret_token": secret_token})
            return HttpResponse(status=200)
        except ValueError:
            raise Http404()

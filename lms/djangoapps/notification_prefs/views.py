from base64 import urlsafe_b64encode, urlsafe_b64decode
from Crypto.Cipher import AES
from django.conf import settings
from django.contrib.auth.models import User
from django.http import Http404, HttpResponse, HttpResponseForbidden, HttpResponseNotAllowed
from hashlib import sha256
from mitxmako.shortcuts import render_to_response
from notification_prefs import NOTIFICATION_PREF_KEY
from user_api.models import UserPreference


class UsernameCodec(object):
    AES_BLOCK_LEN = 16

    def __init__(self):
        hash_ = sha256()
        hash_.update(settings.SECRET_KEY)
        self.cipher = AES.new(hash_.digest())

    def _add_padding(self, str):
        """Return str with PKCS#7 padding added"""
        padding_len = self.AES_BLOCK_LEN - (len(str) % self.AES_BLOCK_LEN)
        return str + (padding_len * chr(padding_len))

    def _remove_padding(self, str):
        """Return str with PKCS#7 padding trimmed"""
        num_pad_bytes = ord(str[-1])
        if num_pad_bytes < 1 or num_pad_bytes > self.AES_BLOCK_LEN or num_pad_bytes >= len(str):
            return None
        return str[:-num_pad_bytes]

    def encode(self, username):
        return urlsafe_b64encode(self.cipher.encrypt(self._add_padding(username)))

    def decode(self, encoded):
        return self._remove_padding(self.cipher.decrypt(urlsafe_b64decode(encoded)))


def _validate_ajax(request):
    """
    Ensure that `request` is valid

    If the request is invalid, an appropriate response is returned. Otherwise,
    None is returned.
    """
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    if not request.user.is_authenticated():
        return HttpResponseForbidden()


def ajax_enable(request):
    """
    A view that enables notifications for the authenticated user

    This view should be invoked by an AJAX POST call. It returns status 204
    (no content) or an error. If notifications were already enabled for this
    user, this has no effect. Otherwise, a preference is created with the
    unsubscribe token (an ecnryption of the username) as the value.unsernam
    """
    validation_response = _validate_ajax(request)
    if validation_response is not None:
        return validation_response

    UserPreference.objects.get_or_create(
        user=request.user,
        key=NOTIFICATION_PREF_KEY,
        defaults={
            "value": UsernameCodec().encode(request.user.username)
        }
    )

    return HttpResponse(status=204)


def ajax_disable(request):
    """
    A view that disables notifications for the authenticated user

    This view should be invoked by an AJAX POST call. It returns status 204
    (no content) or an error.
    """
    validation_response = _validate_ajax(request)
    if validation_response is not None:
        return validation_response

    UserPreference.objects.filter(
        user=request.user,
        key=NOTIFICATION_PREF_KEY
    ).delete()

    return HttpResponse(status=204)


def unsubscribe(request, token):
    """
    A view that disables notifications for a user who may not be authenticated

    This view is meant to be the target of an unsubscribe link. The request
    must be a GET, and the `token` parameter must decrypt to a valid username.

    A 405 will be returned if the request method is not GET. A 404 will be
    returned if the token parameter is missing or if the given token does not
    decrypt to a valid username. On success, the response will contain a page
    indicating success.
    """
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])

    try:
        username = UsernameCodec().decode(token.encode())
        user = User.objects.get(username=username)
    except Exception as e:
        raise Http404(e.message)

    UserPreference.objects.filter(user=user, key=NOTIFICATION_PREF_KEY).delete()

    return render_to_response("unsubscribe.html", {})

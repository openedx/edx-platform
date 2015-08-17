from base64 import urlsafe_b64encode, urlsafe_b64decode
from hashlib import sha256
import json

from Crypto.Cipher import AES
from Crypto import Random
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse
from django.views.decorators.http import require_GET, require_POST

from edxmako.shortcuts import render_to_response
from notification_prefs import NOTIFICATION_PREF_KEY
from openedx.core.djangoapps.user_api.models import UserPreference
from openedx.core.djangoapps.user_api.preferences.api import delete_user_preference


class UsernameDecryptionException(Exception):
    pass


class UsernameCipher(object):
    """
    A transformation of a username to/from an opaque token

    The purpose of the token is to make one-click unsubscribe links that don't
    require the user to log in. To prevent users from unsubscribing other users,
    we must ensure the token cannot be computed by anyone who has this
    source code. The token must also be embeddable in a URL.

    Thus, we take the following steps to encode (and do the inverse to decode):
    1. Pad the UTF-8 encoding of the username with PKCS#7 padding to match the
       AES block length
    2. Generate a random AES block length initialization vector
    3. Use AES-256 (with a hash of settings.SECRET_KEY as the encryption key)
       in CBC mode to encrypt the username
    4. Prepend the IV to the encrypted value to allow for initialization of the
       decryption cipher
    5. base64url encode the result
    """

    @staticmethod
    def _get_aes_cipher(initialization_vector):
        hash_ = sha256()
        hash_.update(settings.SECRET_KEY)
        return AES.new(hash_.digest(), AES.MODE_CBC, initialization_vector)

    @staticmethod
    def _add_padding(input_str):
        """Return `input_str` with PKCS#7 padding added to match AES block length"""
        padding_len = AES.block_size - len(input_str) % AES.block_size
        return input_str + padding_len * chr(padding_len)

    @staticmethod
    def _remove_padding(input_str):
        """Return `input_str` with PKCS#7 padding trimmed to match AES block length"""
        num_pad_bytes = ord(input_str[-1])
        if num_pad_bytes < 1 or num_pad_bytes > AES.block_size or num_pad_bytes >= len(input_str):
            raise UsernameDecryptionException("padding")
        return input_str[:-num_pad_bytes]

    @staticmethod
    def encrypt(username):
        initialization_vector = Random.new().read(AES.block_size)
        aes_cipher = UsernameCipher._get_aes_cipher(initialization_vector)
        return urlsafe_b64encode(
            initialization_vector +
            aes_cipher.encrypt(UsernameCipher._add_padding(username.encode("utf-8")))
        )

    @staticmethod
    def decrypt(token):
        try:
            base64_decoded = urlsafe_b64decode(token)
        except TypeError:
            raise UsernameDecryptionException("base64url")

        if len(base64_decoded) < AES.block_size:
            raise UsernameDecryptionException("initialization_vector")

        initialization_vector = base64_decoded[:AES.block_size]
        aes_encrypted = base64_decoded[AES.block_size:]
        aes_cipher = UsernameCipher._get_aes_cipher(initialization_vector)

        try:
            decrypted = aes_cipher.decrypt(aes_encrypted)
        except ValueError:
            raise UsernameDecryptionException("aes")

        return UsernameCipher._remove_padding(decrypted)


def enable_notifications(user):
    """
    Enable notifications for a user.
    Currently only used for daily forum digests.
    """
    # Calling UserPreference directly because this method is called from a couple of places,
    # and it is not clear that user is always the user initiating the request.
    UserPreference.objects.get_or_create(
        user=user,
        key=NOTIFICATION_PREF_KEY,
        defaults={
            "value": UsernameCipher.encrypt(user.username)
        }
    )


@require_POST
def ajax_enable(request):
    """
    A view that enables notifications for the authenticated user

    This view should be invoked by an AJAX POST call. It returns status 204
    (no content) or an error. If notifications were already enabled for this
    user, this has no effect. Otherwise, a preference is created with the
    unsubscribe token (an encryption of the username) as the value.username
    """
    if not request.user.is_authenticated():
        raise PermissionDenied

    enable_notifications(request.user)

    return HttpResponse(status=204)


@require_POST
def ajax_disable(request):
    """
    A view that disables notifications for the authenticated user

    This view should be invoked by an AJAX POST call. It returns status 204
    (no content) or an error.
    """
    if not request.user.is_authenticated():
        raise PermissionDenied

    delete_user_preference(request.user, NOTIFICATION_PREF_KEY)

    return HttpResponse(status=204)


@require_GET
def ajax_status(request):
    """
    A view that retrieves notifications status for the authenticated user.

    This view should be invoked by an AJAX GET call. It returns status 200,
    with a JSON-formatted payload, or an error.
    """
    if not request.user.is_authenticated():
        raise PermissionDenied

    qs = UserPreference.objects.filter(
        user=request.user,
        key=NOTIFICATION_PREF_KEY
    )

    return HttpResponse(json.dumps({"status": len(qs)}), content_type="application/json")


@require_GET
def set_subscription(request, token, subscribe):  # pylint: disable=unused-argument
    """
    A view that disables or re-enables notifications for a user who may not be authenticated

    This view is meant to be the target of an unsubscribe link. The request
    must be a GET, and the `token` parameter must decrypt to a valid username.
    The subscribe flag feature controls whether the view subscribes or unsubscribes the user, with subscribe=True
    used to "undo" accidentally clicking on the unsubscribe link

    A 405 will be returned if the request method is not GET. A 404 will be
    returned if the token parameter does not decrypt to a valid username. On
    success, the response will contain a page indicating success.
    """
    try:
        username = UsernameCipher().decrypt(token.encode())
        user = User.objects.get(username=username)
    except UnicodeDecodeError:
        raise Http404("base64url")
    except UsernameDecryptionException as exn:
        raise Http404(exn.message)
    except User.DoesNotExist:
        raise Http404("username")

    # Calling UserPreference directly because the fact that the user is passed in the token implies
    # that it may not match request.user.
    if subscribe:
        UserPreference.objects.get_or_create(user=user,
                                             key=NOTIFICATION_PREF_KEY,
                                             defaults={
                                                 "value": UsernameCipher.encrypt(user.username)
                                             })
        return render_to_response("resubscribe.html", {'token': token})
    else:
        UserPreference.objects.filter(user=user, key=NOTIFICATION_PREF_KEY).delete()
        return render_to_response("unsubscribe.html", {'token': token})

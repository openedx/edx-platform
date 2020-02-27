import hashlib
import shortuuid
from django.utils.encoding import force_bytes
from django.conf import settings


def create_hash256(max_length=None):
    """
    Generate a hash that can be used as an application secret
    """
    hash = hashlib.sha256(force_bytes(shortuuid.uuid()))
    hash.update(force_bytes(settings.SECRET_KEY))
    output_hash = hash.hexdigest()
    if max_length is not None and len(output_hash)>max_length:
        return output_hash[:max_length]
    return output_hash

def short_token():
    return create_hash256(max_length=32)


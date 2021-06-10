# lint-amnesty, pylint: disable=missing-module-docstring
# Template used to create cache keys for Integrity Signatures
INTEGRITY_SIGNATURE_CACHE_KEY_TPL = 'integrity-signature-{course_id}-{username}'


def get_integrity_signature_cache_key(username, course_id):
    """
    Util function to help form the cache key for integrity signature
    """
    return INTEGRITY_SIGNATURE_CACHE_KEY_TPL.format(
        username=username,
        course_id=course_id,
    )

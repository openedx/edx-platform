import logging
import warnings

from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.core.cache import cache

from ratelimitbackend.backends import RateLimitModelBackend
from ratelimitbackend.exceptions import RateLimitException

logger = logging.getLogger('ratelimitbackend')


class MineducMixin(RateLimitModelBackend):
    """
    Implementacion para permitir login con usuario
    MINEDUC project require login: usuario = password = CEDULA
    Esto causa un problema de seguridad.
    Requerimiento basado en 'usabilidad' desde el area PMO
    """

    def mineduc_authenticate(self, username, password):
        try:
            if '@' in username:
                user = User.objects.get(email=username)
            else:
                user = User.objects.get(username=username)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None
        
    def authenticate(self, **kwargs):
        request = kwargs.pop('request', None)
        username = kwargs[self.username_key]
        if request is not None:
            counts = self.get_counters(request)
            if sum(counts.values()) >= self.requests:
                logger.warning(
                    u"Login rate-limit reached: username '{0}', IP {1}".format(
                        username, self.get_ip(request),
                    )
                )
                raise RateLimitException('Rate-limit reached', counts)
        else:
            warnings.warn(u"No request passed to the backend, unable to "
                          u"rate-limit. Username was '%s'" % username,
                          stacklevel=2)
        username = request.POST.get('email') and request.POST.get('email') or request.POST.get('username')
        user = self.mineduc_authenticate(username, kwargs['password'])
        if user is None and request is not None:
            logger.info(
                u"Login failed: username '{0}', IP {1}".format(
                    username,
                    self.get_ip(request),
                )
            )
            cache_key = self.get_cache_key(request)
            self.cache_incr(cache_key)
        return user

    def get_counters(self, request):
        return cache.get_many(self.keys_to_check(request))

    def keys_to_check(self, request):
        now = datetime.now()
        return [
            self.key(
                request,
                now - timedelta(minutes=minute),
            ) for minute in range(self.minutes + 1)
        ]

    def get_cache_key(self, request):
        return self.key(request, datetime.now())

    def key(self, request, dt):
        return '%s%s-%s' % (
            self.cache_prefix,
            self.get_ip(request),
            dt.strftime('%Y%m%d%H%M'),
        )

    def get_ip(self, request):
        return request.META['REMOTE_ADDR']

    def cache_incr(self, key):
        """
        Non-atomic cache increment operation. Not optimal but
        consistent across different cache backends.
        """
        cache.set(key, cache.get(key, 0) + 1, self.expire_after())

    def expire_after(self):
        """Cache expiry delay"""
        return (self.minutes + 1) * 60

    
class MineducModelBackend(MineducMixin):
    pass

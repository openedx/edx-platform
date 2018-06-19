"""
Unit tests for safe_endpoints Middleware.
"""
import ddt

from django.test import TestCase
from rest_framework.authentication import SessionAuthentication
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework.decorators import api_view
from rest_framework.views import APIView

from openedx.core.djangolib.testing.utils import get_mock_request

from ..middleware import EnsureJWTAuthSettingsMiddleware


class MockIncludedPermissionClass(object): pass
class MockRequiredPermissionClass(object): pass


def mock_auth_decorator(include_jwt_auth=True):
    def _decorator(f):
        f.permission_classes = (MockIncludedPermissionClass,)
        f.authentication_classes = (SessionAuthentication,)
        if include_jwt_auth:
            f.authentication_classes += (JSONWebTokenAuthentication,)
        return f
    return _decorator


@api_view(["GET"])
@mock_auth_decorator(include_jwt_auth=False)
def mock_function_view(request): pass


@api_view(["GET"])
@mock_auth_decorator(include_jwt_auth=True)
def mock_function_view_with_jwt(request): pass


@mock_auth_decorator(include_jwt_auth=False)
class MockClassAPIView(APIView):
    pass


@mock_auth_decorator(include_jwt_auth=True)
class MockClassAPIViewWithJwt(APIView):
    pass


@ddt.ddt
class TestEnsureJWTAuthSettingsMiddleware(TestCase):
    def setUp(self):
        super(TestEnsureJWTAuthSettingsMiddleware, self).setUp()
        self.request = get_mock_request()

    @ddt.data(
        (mock_function_view, False),
        (mock_function_view_with_jwt, True),
        (MockClassAPIView, False),
        (MockClassAPIViewWithJwt, True),
    )
    @ddt.unpack
    def test_views(self, view, includes_required_permission):
        middleware = EnsureJWTAuthSettingsMiddleware()
        middleware.required_permission_classes = (MockRequiredPermissionClass,)

        view_class = getattr(view, 'view_class', view)

        self.assertNotIn(MockRequiredPermissionClass, view_class.permission_classes)

        middleware.process_view(self.request, view, None, None)

        if includes_required_permission:
            self.assertIn(MockRequiredPermissionClass, view_class.permission_classes)
        else:
            self.assertNotIn(MockRequiredPermissionClass, view_class.permission_classes)

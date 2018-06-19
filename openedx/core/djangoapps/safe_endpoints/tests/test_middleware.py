"""
Unit tests for safe_endpoints Middleware.
"""
import ddt
from itertools import product

from django.test import TestCase
from rest_framework.authentication import SessionAuthentication
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework.decorators import api_view
from rest_framework.views import APIView

from openedx.core.djangolib.testing.utils import get_mock_request

from ..middleware import EnsureJWTAuthSettingsMiddleware


class MockIncludedPermissionClass(object):
    pass


class MockRequiredPermissionClass(object):
    pass


def mock_auth_decorator(include_jwt_auth=True, include_required_perm=True):
    def _decorator(f):
        f.permission_classes = (MockIncludedPermissionClass,)
        f.authentication_classes = (SessionAuthentication,)
        if include_jwt_auth:
            f.authentication_classes += (JSONWebTokenAuthentication,)
        if include_required_perm:
            f.permission_classes += (MockRequiredPermissionClass,)
        return f
    return _decorator


@ddt.ddt
class TestEnsureJWTAuthSettingsMiddleware(TestCase):
    def setUp(self):
        super(TestEnsureJWTAuthSettingsMiddleware, self).setUp()
        self.request = get_mock_request()
        self.middleware = EnsureJWTAuthSettingsMiddleware()
        self.middleware._required_permission_classes = (MockRequiredPermissionClass,)

    def _assert_included(self, item, iterator, should_be_included):
        if should_be_included:
            self.assertIn(item, iterator)
        else:
            self.assertNotIn(item, iterator)

    @ddt.data(
        *product(
            (True, False),
            (True, False),
            (True, False),
        )
    )
    @ddt.unpack
    def test_class_views(self, use_function_view, include_jwt_auth, include_required_perm):
        @mock_auth_decorator(include_jwt_auth=include_jwt_auth, include_required_perm=include_required_perm)
        class MockClassView(APIView):
            pass

        @api_view(["GET"])
        @mock_auth_decorator(include_jwt_auth=include_jwt_auth, include_required_perm=include_required_perm)
        def mock_function_view(request):
            pass

        view = mock_function_view if use_function_view else MockClassView    
        view_class = view.view_class if use_function_view else view

        self._assert_included(
            JSONWebTokenAuthentication,
            view_class.authentication_classes,
            should_be_included=include_jwt_auth,
        )

        self.middleware.process_view(self.request, view, None, None)

        self._assert_included(
            MockRequiredPermissionClass,
            view_class.permission_classes,
            should_be_included=include_required_perm or include_jwt_auth,
        )

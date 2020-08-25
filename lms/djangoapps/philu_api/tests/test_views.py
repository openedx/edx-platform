import json

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import RequestFactory, TestCase
from mock import patch

from lms.djangoapps.philu_api.views import assign_user_badge


def assign_badge_request_body(uid, bid, cid, token):
    return {
        "user_id": uid,
        "badge_id": bid,
        "community_id": cid,
        "token": token
    }


class BadgeAssignViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.assign_path = reverse('assign_user_badge')

    @patch('lms.djangoapps.philu_api.views.UserBadge.assign_badge')
    def test_assign_user_badge_wrong_token(self, mock_userbadge_assign_badge):
        request_body = assign_badge_request_body("16", "1", "-1", "wrong_token")

        request = self.factory.post(self.assign_path,
                                    data=json.dumps(request_body),
                                    content_type='application/json')
        response = assign_user_badge(request)

        assert not mock_userbadge_assign_badge.called
        self.assertEqual(response.status_code, 403)

    @patch('lms.djangoapps.philu_api.views.UserBadge.assign_badge')
    def test_assign_user_badge(self, mock_userbadge_assign_badge):
        request_body = assign_badge_request_body("16", "1", "-1", settings.NODEBB_MASTER_TOKEN)

        request = self.factory.post(self.assign_path,
                                    data=json.dumps(request_body),
                                    content_type='application/json')
        response = assign_user_badge(request)

        assert mock_userbadge_assign_badge.called
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '{"success": true}')

    @patch('lms.djangoapps.philu_api.views.UserBadge.assign_badge')
    def test_assign_user_badge_exception(self, mock_userbadge_assign_badge):
        request_body = assign_badge_request_body("16", "1", "-1", settings.NODEBB_MASTER_TOKEN)
        mock_userbadge_assign_badge.side_effect = Exception()

        request = self.factory.post(self.assign_path,
                                    data=json.dumps(request_body),
                                    content_type='application/json')
        response = assign_user_badge(request)

        assert mock_userbadge_assign_badge.called
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, '{"message": "", "success": false}')

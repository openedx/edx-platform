"""
 API urls to communicate with nodeBB
"""

from django.conf.urls import url

from lms.djangoapps.philu_api.views import (
    MailChimpDataSyncAPI,
    PlatformSyncService,
    ThirdPartyResultDataSyncAPI,
    UpdatePromptClickRecord,
    assign_user_badge,
    download_pdf_file,
    get_user_chat,
    get_user_data,
    mark_user_chat_read,
    resend_activation_email,
    send_alquity_fake_confirmation_email
)

urlpatterns = [
    url(r'platform/sync/service/', PlatformSyncService.as_view(), name='get_shared_data'),
    url(r'mailchimp/sync/enrollments/', MailChimpDataSyncAPI.as_view(), name='sync_user_data_with_mailchimp'),
    url(r'thirdparty/survey/results/', ThirdPartyResultDataSyncAPI.as_view(), name='get_survey_results'),
    url(r'profile/update/', PlatformSyncService.as_view(), name='update_community_profile_update'),
    url(r'profile/chats/?$', get_user_chat, name='get_user_chat'),
    url(r'profile/data/?$', get_user_data, name='get_user_data'),
    url(r'profile/chats/mark/?$', mark_user_chat_read, name='mark_user_chat_read'),
    url(r'download_pdf_file/$', download_pdf_file, name='download_pdf_file'),
    url(r'send_alquity_email/$', send_alquity_fake_confirmation_email, name='send_alquity_fake_confirmation_email'),
    url(r'record_prompt_click/$', UpdatePromptClickRecord.as_view(), name='record_prompt_click'),
    url(r'assign_badge/$', assign_user_badge, name='assign_user_badge'),
    url(r'resend_activation_email/$', resend_activation_email, name='resend_activation_email'),
]

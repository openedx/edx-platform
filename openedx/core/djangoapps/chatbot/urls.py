from django.urls import path

from . import views

urlpatterns = [
    path("query/<session_id>/<int:skip>/<int:limit>/", views.chatbot_fetch_query_list_view),
    path("query/request/", views.chatbot_query_view),
    path("query/retry/", views.chatbot_retry_query_view),
    path("query/cancel/", views.chatbot_cancel_query_view),
    path("query/vote/", views.chatbot_vote_response_view),
    path("session/<int:skip>/<int:limit>/", views.chatbot_fetch_session_list_view),
    path("session/new/", views.chatbot_start_new_session_view),
]

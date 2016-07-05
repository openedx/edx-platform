from django.conf.urls import patterns, url

from appsembler.ps_user_api import views

urlpatterns = patterns(
    '',
    url(r'^v1/accounts/create', views.CreateUserAccountView.as_view(), name="create_user_account_api"),
    url(r'^v1/accounts/(?P<username>[\w.+-]+)', views.GetUserAccountView.as_view(), name="get_user_account_api"),
)
from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.litlbot, name='index'),
    url(r'^slack/(?P<bot_name>\w+)/register/auth/$', views.slack_bot_register_auth, name='slack_bot_register_auth'),
    url(r'^slack/(?P<bot_name>\w+)/oauth/$', views.slack_bot_oauth, name='slack_bot_oauth'),
    url(r'^slack/(?P<bot_name>\w+)/hook/$', views.slack_bot_hook, name='slack_bot_hook'),
    url(r'^slack/(?P<bot_name>\w+)/events/$', views.slack_bot_events)
]

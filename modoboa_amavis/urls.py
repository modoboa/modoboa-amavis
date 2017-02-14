"""Amavis urls."""

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name="index"),
    url(r'^listing/$', views._listing, name="_mail_list"),
    url(r'^listing/page/$', views.listing_page, name="mail_page"),
    url(r'^getmailcontent/(?P<mail_id>[\w\-\+]+)/$', views.getmailcontent,
        name="mailcontent_get"),
    url(r'^process/$', views.process, name="mail_process"),
    url(r'^delete/(?P<mail_id>[\w\-\+]+)/$', views.delete, name="mail_delete"),
    url(r'^release/(?P<mail_id>[\w\-\+]+)/$', views.release,
        name="mail_release"),
    url(r'^markspam/(?P<mail_id>[\w\-\+]+)/$', views.mark_as_spam,
        name="mail_mark_as_spam"),
    url(r'^markham/(?P<mail_id>[\w\-\+]+)/$', views.mark_as_ham,
        name="mail_mark_as_ham"),
    url(r'^learning_recipient/$', views.learning_recipient,
        name="learning_recipient_set"),
    url(r'^(?P<mail_id>[\w\-\+]+)/$', views.viewmail, name="mail_detail"),
    url(r'^(?P<mail_id>[\w\-\+]+)/headers/$', views.viewheaders,
        name="headers_detail"),
]

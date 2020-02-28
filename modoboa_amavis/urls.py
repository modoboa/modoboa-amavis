# -*- coding: utf-8 -*-

"""Amavis urls."""

from django.urls import path

from . import views

app_name = 'modoboa_amavis'

urlpatterns = [
    path('', views.index, name="index"),
    path('listing/', views._listing, name="_mail_list"),
    path('listing/page/', views.listing_page, name="mail_page"),
    path('getmailcontent/<str:mail_id>/', views.getmailcontent,
         name="mailcontent_get"),
    path('process/', views.process, name="mail_process"),
    path('delete/<str:mail_id>/', views.delete, name="mail_delete"),
    path('release/<str:mail_id>/', views.release,
         name="mail_release"),
    path('markspam/<str:mail_id>/', views.mark_as_spam,
         name="mail_mark_as_spam"),
    path('markham/<str:mail_id>/', views.mark_as_ham,
         name="mail_mark_as_ham"),
    path('learning_recipient/', views.learning_recipient,
         name="learning_recipient_set"),
    path('<str:mail_id>/', views.viewmail, name="mail_detail"),
    path('<str:mail_id>/headers/', views.viewheaders,
         name="headers_detail"),
]

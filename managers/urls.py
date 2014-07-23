
from django.conf.urls import url

from managers import views

urlpatterns = [
    url(r'^custom_admin/anonymous_login/$', views.anonymous_login_view, name='anonymous_login'),
    url(r'^custom_admin/end_anonymous_session/$', views.end_anonymous_session_view, name='end_anonymous_session'),
    url(r'^manager_directory/(?P<managerTitle>[-\w]+)/$', views.manager_view, name='view_manager'),
    url(r'^manager_directory/$', views.list_managers_view, name='list_managers'),
    url(r'^custom_admin/add_manager/$', views.add_manager_view, name='add_manager'),
    url(r'^custom_admin/managers/(?P<managerTitle>[-\w]+)/$', views.edit_manager_view, name='edit_manager'),
    url(r'^custom_admin/managers/$', views.meta_manager_view, name='meta_manager'),
    url(r'^custom_admin/request_types/(?P<typeName>[-\w]+)/$', views.edit_request_type_view, name='edit_request_type'),
    url(r'^custom_admin/request_types/$', views.manage_request_types_view, name='manage_request_types'),
    url(r'^custom_admin/add_request_type/$', views.add_request_type_view, name='add_request_type'),
    url(r'^profile/(?P<targetUsername>[-\w]+)/requests/$', views.list_user_requests_view, name='list_user_requests'),
    url(r'^requests/(?P<requestType>[-\w]+)/$', views.requests_view, name='requests'),
    url(r'^archives/all_requests/$', views.all_requests_view, name='all_requests'),
    url(r'^requests/(?P<requestType>[-\w]+)/all/$', views.list_all_requests_view, name='list_all_requests'),
    url(r'^my_requests/$', views.my_requests_view, name='my_requests'),
    url(r'^request/(?P<request_pk>\d+)/$', views.request_view, name='view_request'),
    url(r'^announcements/$', views.announcements_view, name='announcements'),
    url(r'^announcements/(?P<announcement_pk>\d+)/$', views.announcement_view, name='view_announcement'),
    url(r'^announcements/(?P<announcement_pk>\d+)/edit/$', views.edit_announcement_view, name='edit_announcement'),
    url(r'^announcements/all/$', views.all_announcements_view, name='all_announcements'),
]

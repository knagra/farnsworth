
from django.conf.urls import url

from workshift import views

urlpatterns = [
	url(r"^workshift/start/?$", views.start_semester_view, name="start_semester"),
	url(r"^workshift(?:/(?P<sem_url>\w+\d+))?/?$", views.view_semester, name="view_semester"),
	url(r"^workshift(?:/(?P<sem_url>\w+\d+))?/profile/(?P<profile_pk>\d+)/?$", views.profile_view, name="profile"),
	url(r"^workshift(?:/(?P<sem_url>\w+\d+))?/profile/(?P<profile_pk>\d+)/preferences/?$", views.preferences_view, name="preferences"),
	url(r"^workshift(?:/(?P<sem_url>\w+\d+))?/manage/?$", views.manage_view, name="manage"),
	url(r"^workshift(?:/(?P<sem_url>\w+\d+))?/manage/assign_shifts/?$", views.assign_shifts_view, name="assign_shifts"),
	url(r"^workshift/add_shift/?$", views.add_shift_view, name="add_shift"),
	url(r"^workshift(?:/(?P<sem_url>\w+\d+))?/shift/(?P<shift_pk>\d+)/?$", views.shift_view, name="view_shift"),
	url(r"^workshift(?:/(?P<sem_url>\w+\d+))?/shift/(?P<shift_pk>\d+)/edit/?$", views.edit_shift_view, name="edit_shift"),
	url(r"^workshift(?:/(?P<sem_url>\w+\d+))?/instance/(?P<instance_pk>\d+)/?$", views.instance_view, name="view_instance"),
	url(r"^workshift(?:/(?P<sem_url>\w+\d+))?/instance/(?P<instance_pk>\d+)/edit/?$", views.edit_instance_view, name="edit_instance"),
	url(r"^workshift(?:/(?P<sem_url>\w+\d+))?/once/(?P<one_time_pk>\d+)/?$", views.one_time_view, name="view_one_time"),
	url(r"^workshift(?:/(?P<sem_url>\w+\d+))?/once/(?P<one_time_pk>\d+)/edit/?$", views.edit_one_time_view, name="edit_one_time"),
	url(r"^workshift/types/?$", views.list_types_view, name="list_types"),
	url(r"^workshift/type/(?P<type_pk>\d+)/?$", views.type_view, name="view_type"),
	url(r"^workshift/type/(?P<type_pk>\d+)/edit/?$", views.edit_type_view, name="edit_type"),
]

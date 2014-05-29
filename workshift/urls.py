
from django.conf.urls import url

from workshift import views

urlpatterns = [
	url(r"^workshift/$", views.main_view, name="main"),
	url(r"^workshift/start_semester/$", views.start_semester_view, name="start_semester"),
	url(r"^workshift/(P<sem_url>[0-9]{5})/$", views.view_semester, name="view_semester"),
	url(r"^workshift/(P<sem_url>[0-9]{5})/me/$", views.my_profile_view, name="my_profile"),
	url(r"^workshift/(P<sem_url>[0-9]{5})/me/preferences/$", views.my_preferences_view, name="my_preferences"),
	url(r"^workshift/(P<sem_url>[0-9]{5})/profile/(P<profile_pk>\d+)/$", views.profile_view, name="profile"),
	url(r"^workshift/(P<sem_url>[0-9]{5})/profile/(P<profile_pk>\d+)/preferences/$", views.preferences_view, name="preferences"),
	url(r"^workshift/(P<sem_url>[0-9]{5})/manage/$", views.manage_view, name="manage"),
	url(r"^workshift/(P<sem_url>[0-9]{5})/manage/assign_shifts/$", views.assign_shifts_view, name="assign_shifts"),
	url(r"^workshift/(P<sem_url>[0-9]{5})/manage/add_shift/$", views.add_shift_view, name="add_shift"),
	url(r"^workshift/(P<sem_url>[0-9]{5})/shifts/(P<shift_pk>\d+)/$", views.shift_view, name="view_shift"),
	url(r"^workshift/(P<sem_url>[0-9]{5})/shifts/(P<shift_pk>\d+)/edit$", views.edit_shift_view, name="edit_shift"),
	url(r"^workshift/(P<sem_url>[0-9]{5})/instance/(P<instance_pk>\d+)/$", views.instance_view, name="view_instance"),
	url(r"^workshift/(P<sem_url>[0-9]{5})/instance/(P<instance_pk>\d+)/edit$", views.edit_instance_view, name="edit_instance"),
	url(r"^workshift/(P<sem_url>[0-9]{5})/once/(P<instance_pk>\d+)/$", views.instance_view, name="view_onc_off"),
	url(r"^workshift/(P<sem_url>[0-9]{5})/once/(P<instance_pk>\d+)/edit$", views.edit_instance_view, name="edit_one_off"),
]

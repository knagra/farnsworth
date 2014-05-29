
from django.conf.urls import url

from workshift import views

urlpatterns = [
	url(r"^workshift/$", views.main_view, name="main"),
	url(r"^workshift/start_semester/$", views.start_semester_view, name="start_semester"),
	url(r"^workshift/(P<sem_url>[0-9]{5})/$", views.view_semester, name="view_semester"),
	url(r"^workshift/(P<sem_url>[0-9]{5})/me$", views.my_profile_view, name="my_profile"),
	url(r"^workshift/(P<sem_url>[0-9]{5})/me/preferences/$", views.my_preferences_view, name="my_preferences"),
	url(r"^workshift/(P<sem_url>[0-9]{5})/profile/$", views.profile_view, name="profile"),
	url(r"^workshift/(P<sem_url>[0-9]{5})/profile/preferences/$", views.preferences_view, name="preferences"),
	url(r"^workshift/(P<sem_url>[0-9]{5})/manage/$", views.manage_view, name="manage"),
	url(r"^workshift/(P<sem_url>[0-9]{5})/manage/assign_shifts/$", views.assign_shifts_view, name="assign_shifts"),
	url(r"^workshift/(P<sem_url>[0-9]{5})/manage/add_shift/$", views.add_shift_view, name="add_shift"),
	url(r"^workshift/(P<sem_url>[0-9]{5})/shifts/(P<shift_title>\w+)/$", views.shift_view, name="view_shift"),
	url(r"^workshift/(P<sem_url>[0-9]{5})/shifts/(P<shift_title>\w+)/edit$", views.edit_shift_view, name="edit_shift"),
	url(r"^workshift/(P<sem_url>[0-9]{5})/instance/(P<instance_pk>\w+)/$", views.instance_view, name="view_instance"),
	url(r"^workshift/(P<sem_url>[0-9]{5})/instance/(P<instance_pk>\w+)/edit$", views.edit_instance_view, name="edit_instance"),
]


from django.conf.urls import url

from workshift import views

urlpatterns = [
	url(r"^workshift/start/$", views.start_semester_view, name="start_semester"),
	url(r"^workshift(?:/(?P<sem_url>\w+\d+))?/$", views.view_semester, name="view_semester"),
	url(r"^workshift(?:/(?P<sem_url>\w+\d+))?/profile/(?P<targetUsername>\w+)/$", views.profile_view, name="profile"),
	url(r"^workshift(?:/(?P<sem_url>\w+\d+))?/profile/(?P<targetUsername>\w+)/preferences/$", views.preferences_view, name="preferences"),
	url(r"^workshift(?:/(?P<sem_url>\w+\d+))?/profiles/$", views.profiles_view, name="profiles"),
	url(r"^workshift(?:/(?P<sem_url>\w+\d+))?/manage/$", views.manage_view, name="manage"),
	url(r"^workshift(?:/(?P<sem_url>\w+\d+))?/manage/assign_shifts/$", views.assign_shifts_view, name="assign_shifts"),
	#: Maybe get rid of add_workshifter and allow anyone who is Resident or Boarder to create a workshift profile when accessing a workshift_profile_required view for current semester
	url(r"^workshift(?:/(?P<sem_url>\w+\d+))?/manage/add_workshifter/$", views.add_workshifter_view, name="add_workshifter"),
	url(r"^workshift(?:/(?P<sem_url>\w+\d+))?/manage/add_pool/$", views.add_pool_view, name="add_pool"),
	url(r"^workshift(?:/(?P<sem_url>\w+\d+))?/manage/add_shift/$", views.add_shift_view, name="add_shift"),
	url(r"^workshift(?:/(?P<sem_url>\w+\d+))?/pool/(?P<pk>\d+)/$", views.pool_view, name="view_pool"),
	url(r"^workshift(?:/(?P<sem_url>\w+\d+))?/pool/(?P<pk>\d+)/edit/$", views.edit_pool_view, name="edit_pool"),
	url(r"^workshift(?:/(?P<sem_url>\w+\d+))?/shift/(?P<pk>\d+)/$", views.shift_view, name="view_shift"),
	url(r"^workshift(?:/(?P<sem_url>\w+\d+))?/shift/(?P<pk>\d+)/edit/$", views.edit_shift_view, name="edit_shift"),
	url(r"^workshift(?:/(?P<sem_url>\w+\d+))?/instance/(?P<pk>\d+)/$", views.instance_view, name="view_instance"),
	url(r"^workshift(?:/(?P<sem_url>\w+\d+))?/instance/(?P<pk>\d+)/edit/$", views.edit_instance_view, name="edit_instance"),
	url(r"^workshift/types/$", views.list_types_view, name="list_types"),
	url(r"^workshift/type/(?P<pk>\d+)/$", views.type_view, name="view_type"),
	url(r"^workshift/type/(?P<pk>\d+)/edit/$", views.edit_type_view, name="edit_type"),
]

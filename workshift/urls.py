from django.conf.urls import url

from workshift import views

urlpatterns = [
	url(r"^workshift/$", views.main_view, name="main"),
	url(r"^workshift/preferences/(P<semester>\w+)/$", views.preferences_view, name="preferences"),
	url(r"^workshift/manage/$", views.manage_view, name="manage"),
	url(r"^workshift/manage/start_semester/$", views.start_semester_view, name="start_semester"),
	url(r"^workshift/manage/assign_shifts/$", views.assign_shifts_view, name="assign_shifts"),
	url(r"^workshift/manage/add_shift/$", views.add_shift_view, name="add_shift"),
	url(r"^workshift/shifts/(P<shift_title>\w+)/$", views.shift_view, name="view_shift"),
	url(r"^workshift/shifts/(P<shift_title>\w+)/edit$", views.edit_shift_view, name="edit_shift"),
]

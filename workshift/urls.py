
from django.conf.urls import url

from workshift import views

base = r"workshift(?:/(?P<sem_url>\w+\d+))?"

urlpatterns = [
    url(
        r"^workshift/start/$",
        views.start_semester_view,
        name="start_semester",
    ),
    url(
        base + r"/$",
        views.semester_view,
        name="view_semester",
    ),
    url(
        base + r"/info/$",
        views.semester_info_view,
        name="semester_info",
    ),
    url(
        base + r"/open/$",
        views.open_shifts_view,
        name="view_open",
    ),
    url(
        base + r"/profile/(?P<targetUsername>[-\w]+)/$",
        views.profile_view,
        name="profile",
    ),
    url(
        base + r"/profile/(?P<targetUsername>[-\w]+)/edit/$",
        views.edit_profile_view,
        name="edit_profile",
    ),
    url(
        base + r"/profile/(?P<targetUsername>[-\w]+)/preferences/$",
        views.preferences_view,
        name="preferences",
    ),
    url(
        base + r"/profiles/$",
        views.profiles_view,
        name="profiles",
    ),
    url(
        base + r"/manage/$",
        views.manage_view,
        name="manage",
    ),
    url(
        base + r"/manage/assign_shifts/$",
        views.assign_shifts_view,
        name="assign_shifts",
    ),
    #: Maybe get rid of add_workshifter and allow anyone who is Resident or
    #Boarder to create a workshift profile when accessing a
    #workshift_profile_required view for current semester
    url(
        base + r"/manage/add_workshifter/$",
        views.add_workshifter_view,
        name="add_workshifter",
    ),
    url(
        base + r"/manage/add_pool/$",
        views.add_pool_view,
        name="add_pool",
    ),
    url(
        base + r"/manage/fill_shifts/$",
        views.fill_shifts_view,
        name="fill_shifts",
    ),
    url(
        base + r"/manage/adjust_hours/$",
        views.adjust_hours_view,
        name="adjust_hours",
    ),
    url(
        base + r"/manage/easy_fill/$",
        views.fill_shifts_view,
        name="easy_fill",
    ),
    url(
        base + r"/manage/add_shift/$",
        views.add_shift_view,
        name="add_shift",
    ),
    url(
        base + r"/manage/fine_date/$",
        views.fine_date_view,
        name="fine_date",
    ),
    url(
        base + r"/pool/(?P<pk>\d+)/$",
        views.pool_view,
        name="view_pool",
    ),
    url(
        base + r"/pool/(?P<pk>\d+)/edit/$",
        views.edit_pool_view,
        name="edit_pool",
    ),
    url(
        base + r"/shift/(?P<pk>\d+)/$",
        views.shift_view,
        name="view_shift",
    ),
    url(
        base + r"/shift/(?P<pk>\d+)/edit/$",
        views.edit_shift_view,
        name="edit_shift",
    ),
    url(
        base + r"/instance/(?P<pk>\d+)/$",
        views.instance_view,
        name="view_instance",
    ),
    url(
        base + r"/instance/(?P<pk>\d+)/edit/$",
        views.edit_instance_view,
        name="edit_instance",
    ),
    url(
        base + r"/types/$",
        views.list_types_view,
        name="list_types",
    ),
    url(
        base + r"/type/(?P<pk>\d+)/$",
        views.type_view,
        name="view_type",
    ),
    url(
        base + r"/type/(?P<pk>\d+)/edit/$",
        views.edit_type_view,
        name="edit_type",
    ),
]

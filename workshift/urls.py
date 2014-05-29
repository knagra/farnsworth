from django.conf.urls import url

from workshift import views

urlpatterns = [
	url(r"^workshift/$", views.workshift_view, name="workshift_view"),
]

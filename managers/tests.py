"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.contrib.auth.models import User
from django.test import TestCase
from farnsworth.settings import MESSAGES
from threads.models import UserProfile
from managers.models import ProfileRequest, Manager, RequestType, Request

class ManagementPermission(TestCase):
	def setUp(self):
		self.u = User.objects.create_user(username="u", email="u@email.com", password="pwd")
		self.st = User.objects.create_user(username="st", email="st@email.com", password="pwd")
		self.pu = User.objects.create_user(username="pu", email="su@email.com", password="pwd")
		self.su = User.objects.create_user(username="su", email="su@email.com", password="pwd")
		self.np = User.objects.create_user(username="np", email="np@email.com", password="pwd")
		self.st.is_staff = True
		self.su.is_staff, self.su.is_superuser = True, True
		self.u.save()
		self.st.save()
		self.pu.save()
		self.su.save()
		self.np.save()

		president = Manager(title="House President", url_title="president",
				    president=True)
		president.incumbent = UserProfile.objects.get(user=self.pu)
		president.save()

		food = RequestType(name="Food", url_name="food", enabled=True)
		food.save()
		food.managers = [president]
		food.save()

		self.request = Request(owner=UserProfile.objects.get(user=self.u),
				       body="request body", request_type=food)
		self.request.save()

		UserProfile.objects.get(user=self.np).delete()
		self.pr = ProfileRequest(username="pr", email="pr@email.com",
					 affiliation=UserProfile.STATUS_CHOICES[0][0])
		self.pr.save()

	def _admin_required(self, url, success_target=None):
		response = self.client.get(url)
		self.assertRedirects(response, "/login/")

		self.client.login(username="np", password="pwd")
		response = self.client.get(url, follow=True)
		self.assertRedirects(response, "/landing/")
		self.assertIn(MESSAGES["NO_PROFILE"], response.content)
		self.client.logout()

		self.client.login(username="u", password="pwd")
		response = self.client.get(url, follow=True)
		self.assertRedirects(response, "/")
		self.assertIn(MESSAGES["ADMINS_ONLY"], response.content)
		self.client.logout()

		self.client.login(username="st", password="pwd")
		response = self.client.get(url, follow=True)
		self.assertRedirects(response, "/")
		self.assertIn(MESSAGES["ADMINS_ONLY"], response.content)
		self.client.logout()

		self.client.login(username="su", password="pwd")
		response = self.client.get(url)
		if success_target is None:
			self.assertEqual(response.status_code, 200)
		else:
			self.assertRedirects(response, success_target)
		self.client.logout()

	def _president_admin_required(self, url, success_target=None):
		response = self.client.get(url)
		self.assertRedirects(response, "/login/")

		self.client.login(username="np", password="pwd")
		response = self.client.get(url, follow=True)
		self.assertRedirects(response, "/landing/")
		self.assertIn(MESSAGES["NO_PROFILE"], response.content)
		self.client.logout()

		self.client.login(username="u", password="pwd")
		response = self.client.get(url, follow=True)
		self.assertRedirects(response, "/")
		self.assertIn(MESSAGES["PRESIDENTS_ONLY"], response.content)
		self.client.logout()

		self.client.login(username="st", password="pwd")
		response = self.client.get(url, follow=True)
		self.assertRedirects(response, "/")
		self.assertIn(MESSAGES["PRESIDENTS_ONLY"], response.content)
		self.client.logout()

		self.client.login(username="su", password="pwd")
		response = self.client.get(url)
		if success_target is None:
			self.assertEqual(response.status_code, 200)
		else:
			self.assertRedirects(response, success_target)
		self.client.logout()

		self.client.login(username="pu", password="pwd")
		response = self.client.get(url)
		if success_target is None:
			self.assertEqual(response.status_code, 200)
		else:
			self.assertRedirects(response, success_target)
		self.client.logout()

	def _profile_required(self, url, success_target=None):
		response = self.client.get(url)
		self.assertRedirects(response, "/login/")

		self.client.login(username="np", password="pwd")
		response = self.client.get(url, follow=True)
		self.assertRedirects(response, "/landing/")
		self.assertIn(MESSAGES["NO_PROFILE"], response.content)
		self.client.logout()

		self.client.login(username="u", password="pwd")
		response = self.client.get(url, follow=True)
		if success_target is None:
			self.assertEqual(response.status_code, 200)
		else:
			self.assertRedirects(response, success_target)
		self.client.logout()

		self.client.login(username="st", password="pwd")
		response = self.client.get(url, follow=True)
		if success_target is None:
			self.assertEqual(response.status_code, 200)
		else:
			self.assertRedirects(response, success_target)
		self.client.logout()

		self.client.login(username="su", password="pwd")
		response = self.client.get(url, follow=True)
		if success_target is None:
			self.assertEqual(response.status_code, 200)
		else:
			self.assertRedirects(response, success_target)
		self.client.logout()

	def test_admin_required(self):
		pages = [
			"profile_requests",
			"profile_requests/{0}".format(self.pr.pk),
			"manage_users",
			"modify_user/{0}".format(self.u.username),
			"add_user",
			"utilities",
			]
		for page in pages:
			self._admin_required("/custom_admin/" + page + "/")
		self._admin_required("/custom_admin/recount/",
				     success_target="/custom_admin/utilities/")
		self._admin_required("/custom_admin/anonymous_login/",
				     success_target="/")
		self._admin_required("/custom_admin/end_anonymous_session/",
				     success_target="/custom_admin/utilities/")

	def test_president_admin_required(self):
		pages = [
			"managers",
			"managers/president",
			"add_manager",
			"request_types",
			"request_types/food",
			"add_request_type",
			]
		for page in pages:
			self._president_admin_required("/custom_admin/" + page + "/")

	def test_profile_required(self):
		pages = [
			"manager_directory",
			"manager_directory/president",
			"profile/{0}/requests".format(self.u.username),
			"requests/food",
			"archives/all_requests",
			"requests/food/all",
			"my_requests",
			"request/{0}".format(self.request.pk),
			"archives/all_announcements",
			]
		for page in pages:
			self._profile_required("/" + page + "/")

	def test_anonymous_user(self):
		self.client.login(username="su", password="pwd")
		response = self.client.get("/custom_admin/anonymous_login/", follow=True)
		self.assertRedirects(response, "/")
		response = self.client.get("/")
		self.assertIn("Anonymous Coward", response.content)

		# Test that we are "Anonymous Coward"?

		self.client.login(username="su", password="pwd")
		response = self.client.get("/custom_admin/end_anonymous_session/", follow=True)
		self.assertRedirects(response, "/custom_admin/utilities/")
		self.assertIn(MESSAGES["ANONYMOUS_SESSION_ENDED"], response.content)

		self.client.logout()

	def test_request_form(self):
		urls = [
			"/resquest/{0}/".format(self.request.pk),
			"/requests/food/",
			]
		for url in urls:
			self.client.login(username="u", password="pwd")
			response = self.client.get(url)
			self.assertNotIn("mark_filled", response.content)
			self.client.logout()

			self.client.login(username="pu", password="pwd")
			response = self.client.get(url)
			self.assertIn("mark_filled", response.content)
			self.client.logout()

	def test_profile_request(self):
		self.client.login(username="su", password="pwd")

		response = self.client.get("/custom_admin/profile_requests/{0}/"
					   .format(self.pr.pk))
		self.assertEqual(response.status_code, 200)
		self.client.logout()

		# Test that we can approve requests?

"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.contrib.auth.models import User
from django.test import TestCase
from farnsworth.settings import MESSAGES
from threads.models import UserProfile
from managers.models import ProfileRequest

class ManagementPermission(TestCase):
	def setUp(self):
		self.u = User.objects.create_user(username="u", email="u@email.com", password="password")
		self.st = User.objects.create_user(username="st", email="st@email.com", password="password")
		self.pu = User.objects.create_user(username="pu", email="su@email.com", password="password")
		self.su = User.objects.create_user(username="su", email="su@email.com", password="password")
		self.np = User.objects.create_user(username="np", email="np@email.com", password="password")
		self.st.is_staff = True
		self.su.is_staff, self.su.is_superuser = True, True
		# self.pu.president = True...
		self.u.save()
		self.st.save()
		self.pu.save()
		self.su.save()
		self.np.save()
		UserProfile.objects.get(user=self.np).delete()
		self.pr = ProfileRequest(username="pr", email="pr@email.com", affiliation=UserProfile.STATUS_CHOICES[0][0])
		self.pr.save()

	def _admin_required(self, url, success_target=None):
		response = self.client.get(url)
		self.assertRedirects(response, "/login/")

		self.client.login(username="np", password="password")
		response = self.client.get(url, follow=True)
		self.assertRedirects(response, "/landing/")
		self.assertIn(MESSAGES["NO_PROFILE"], response.content)
		self.client.logout()

		self.client.login(username="u", password="password")
		response = self.client.get(url, follow=True)
		self.assertRedirects(response, "/")
		self.assertIn(MESSAGES["ADMINS_ONLY"], response.content)
		self.client.logout()

		self.client.login(username="st", password="password")
		response = self.client.get(url, follow=True)
		self.assertRedirects(response, "/")
		self.assertIn(MESSAGES["ADMINS_ONLY"], response.content)
		self.client.logout()

		self.client.login(username="su", password="password")
		response = self.client.get(url)
		if success_target is None:
			self.assertEqual(response.status_code, 200)
		else:
			self.assertRedirects(response, success_target)
		self.client.logout()

	def _profile_required(self, url, success_target=None):
		response = self.client.get(url)
		self.assertRedirects(response, "/login/")

		self.client.login(username="np", password="password")
		response = self.client.get(url, follow=True)
		self.assertRedirects(response, "/landing/")
		self.assertIn(MESSAGES["NO_PROFILE"], response.content)
		self.client.logout()

		self.client.login(username="u", password="password")
		response = self.client.get(url, follow=True)
		if success_target is None:
			self.assertEqual(response.status_code, 200)
		else:
			self.assertRedirects(response, success_target)
		self.client.logout()

		self.client.login(username="st", password="password")
		response = self.client.get(url, follow=True)
		if success_target is None:
			self.assertEqual(response.status_code, 200)
		else:
			self.assertRedirects(response, success_target)
		self.client.logout()

		self.client.login(username="su", password="password")
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
			# "managers",
			# "managers/manager_title",
			# "add_manager",
			# "request_types",
			# "request_types/type_name",
			# "add_request_type",
			]

		for page in pages:
			self._admin_required("/custom_admin/" + page + "/")

		self._admin_required("/custom_admin/recount/",
				     success_target="/custom_admin/utilities/")
		self._admin_required("/custom_admin/anonymous_login/",
				     success_target="/")
		self._admin_required("/custom_admin/end_anonymous_session/",
				     success_target="/custom_admin/utilities/")

	def test_profile_required(self):
		pages = [
			"manager_directory",
			# "manager_directory/manager_title",
			"profile/{0}/requests".format(self.u.username),
			# "requests/request_type"
			"archives/all_requests",
			# "requests/request_type/all",
			"my_requests",
			# "request/request_pk",
			"archives/all_announcements",
			]

		for page in pages:
			self._profile_required("/" + page + "/")
			

	def test_anonymous_user(self):
		self.client.login(username="su", password="password")
		response = self.client.get("/custom_admin/anonymous_login/", follow=True)
		self.assertRedirects(response, "/")
		response = self.client.get("/")
		self.assertIn("Anonymous Coward", response.content)

		# Test that we are "Anonymous Coward"?

		self.client.login(username="su", password="password")
		response = self.client.get("/custom_admin/end_anonymous_session/", follow=True)
		self.assertRedirects(response, "/custom_admin/utilities/")
		self.assertIn(MESSAGES["ANONYMOUS_SESSION_ENDED"], response.content)

		self.client.logout()

	def test_profile_request(self):
		self.client.login(username="su", password="password")

		response = self.client.get("/custom_admin/profile_requests/{0}/"
					   .format(self.pr.pk))
		self.assertEqual(response.status_code, 200)
		self.client.logout()

		# Test that we can approve requests?

"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".
"""

from datetime import datetime, timedelta
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.utils.timezone import utc
from base.models import UserProfile, ProfileRequest
from threads.models import Thread, Message
from managers.models import Manager, Announcement, RequestType, Request
from events.models import Event

class VerifyUser(TestCase):
	def setUp(self):
		self.u = User.objects.create_user(username="u", password="pwd")
		self.u.save()

	def test_user_profile_created(self):
		''' Test that the user profile for a user is automatically created when a user is created. '''
		self.assertEqual(1, UserProfile.objects.filter(user=self.u).count())
		self.assertEqual(self.u, UserProfile.objects.get(user=self.u).user)

	def test_login(self):
		self.assertEqual(True, self.client.login(username="u", password="pwd"))
		self.assertEqual(None, self.client.logout())

	def test_homepage(self):
		response = self.client.get("/", follow=True)
		self.assertRedirects(response, "/landing/")
		self.client.login(username="u", password="pwd")
		response = self.client.get("/")
		self.assertEqual(response.status_code, 200)
		self.client.logout()
		response = self.client.get("/", follow=True)
		self.assertRedirects(response, "/landing/")

class FromHome(TestCase):
	def setUp(self):
		self.u = User.objects.create_user(username="u", password="pwd")
		self.u.save()

		profile = UserProfile.objects.get(user=self.u)
		self.manager = Manager(title="Super Manager", url_title="super")
		self.manager.incumbent = profile
		self.manager.save()

		self.rt = RequestType(name="Super", url_name="super", enabled=True)
		self.rt.save()
		self.rt.managers = [self.manager]
		self.rt.save()

		self.req = Request(owner=profile, request_type=self.rt)
		self.req.save()

		now = datetime.utcnow().replace(tzinfo=utc)
		one_day = timedelta(days=1)
		self.ev = Event(owner=profile, title="Event Title Test",
				start_time=now, end_time=now + one_day)
		self.ev.save()

		self.client.login(username="u", password="pwd")

	def test_homepage_view(self):
		response = self.client.get("/")

		self.assertEqual(response.status_code, 200)
		self.assertIn("Recent Threads", response.content)
		self.assertIn("Recent Announcements", response.content)
		self.assertIn("Today's Events", response.content)
		self.assertIn(self.ev.title, response.content)
		self.assertIn("{0} Requests".format(self.rt.name), response.content)

	def test_homepage_no_requests(self):
		self.req.delete()
		response = self.client.get("/")
		self.assertNotIn("{0} Requests".format(self.rt.name), response.content)

	def test_homepage_requests_filled(self):
		self.req.filled = True
		self.req.save()
		response = self.client.get("/")
		self.assertNotIn("{0} Requests".format(self.rt.name), response.content)

	def test_thread_post(self):
		response = self.client.post("/", {
				"submit_thread_form": "",
				"subject": "Thread Subject Test",
				"body": "Thread Body Text Test",
				 }, follow=True)
		self.assertRedirects(response, "/")
		self.assertIn("Thread Subject Test", response.content)

		thread = Thread.objects.get(subject="Thread Subject Test")
		profile = UserProfile.objects.get(user=self.u)
		self.assertEqual(thread.owner, profile)
		thread.delete()

	def test_announcment_post(self):
		response = self.client.post("/", {
				"post_announcement": "",
				"as_manager": "1",
				"body": "Announcement Body Text Test",
				}, follow=True)
		self.assertRedirects(response, "/")
		self.assertIn("Announcement Body Text Test", response.content)

		announcement = Announcement.objects.get(body="Announcement Body Text Test")
		profile = UserProfile.objects.get(user=self.u)
		self.assertEqual(announcement.incumbent, profile)
		announcement.delete()

	def test_rsvp_post(self):
		response = self.client.post("/", {
				"rsvp": "",
				"event_pk": "{0}".format(self.ev.pk),
				}, follow=True)
		self.assertRedirects(response, "/")
		self.assertIn('title="Un-RSVP"', response.content)

		response = self.client.post("/", {
				"rsvp": "",
				"event_pk": "{0}".format(self.ev.pk),
				}, follow=True)
		self.assertRedirects(response, "/")
		self.assertIn('title="RSVP"', response.content)

class TestRequestAccount(TestCase):
	def setUp(self):
		self.su = User.objects.create_user(username="su", password="pwd")
		self.su.is_staff, self.su.is_superuser = True, True
		self.su.save()

		self.pr = ProfileRequest(username="pr", email="pr@email.com",
					 affiliation=UserProfile.RESIDENT)
		self.pr.save()

	def test_approve_profile_request_view(self):
		self.client.login(username="su", password="pwd")

		response = self.client.get("/custom_admin/profile_requests/{0}/"
					   .format(self.pr.pk))
		self.assertEqual(response.status_code, 200)
		self.assertIn(self.pr.email, response.content)

	def test_approve_profile_request(self):
		self.client.login(username="su", password="pwd")

		username = self.pr.username

		response = self.client.post("/custom_admin/profile_requests/{0}/"
					    .format(self.pr.pk), {
				"username": username,
				"first_name": "first",
				"last_name": "last",
				"email": self.pr.email,
				"phone_number": "",
				"status": self.pr.affiliation,
				"current_room": "",
				"former_rooms": "",
				"former_houses": "",
				"is_active": "on",
				"add_user": "",
				}, follow=True)

		self.assertRedirects(response, "/custom_admin/profile_requests/")
		self.assertIn("User {0} was successfully added".format(username),
			      response.content)

	def test_request_profile(self):
		response = self.client.post("/request_profile/", {
				"username": "request",
				"first_name": "first",
				"last_name": "last",
				"email": "request@email.com",
				"affiliation_with_the_house": UserProfile.RESIDENT,
				"password": "pwd",
				"confirm_password": "pwd",
				}, follow=True)
		self.assertRedirects(response, reverse("external"))

		self.client.login(username="su", password="pwd")
		response = self.client.get("/custom_admin/profile_requests/{0}"
					   .format(self.pr.pk + 1))
		self.assertEqual(response.status_code, 200)

		pr = ProfileRequest.objects.get(username="request")
		self.assertEqual(pr.email, "request@email.com")

class TestProfileRequests(TestCase):
	def test_bad_username(self):
		usernames = [
			"user&name",
			"user.name",
			"user,name",
			"user>name",
			"user<name",
			"user^name",
			"user%name",
			"user:name",
			"user+name",
			"\"username",
			"-username",
			"~username",
			"\'username",
			]

		for username in usernames:
			response = self.client.post("/request_profile/", {
					"username": username,
					"first_name": "first",
					"last_name": "last",
					"email": "request@email.com",
					"affiliation_with_the_house": UserProfile.RESIDENT,
					"password": "pwd",
					"confirm_password": "pwd",
					}, follow=True)
			self.assertEqual(response.status_code, 200)
			self.assertIn("Invalid username. Must be characters A-Z, a-z, 0-9, or &quot;_&quot;",
				      response.content)

	def test_good_username(self):
		usernames = [
			"u",
			"U",
			"1",
			"_",
			"____________________",
			"aA_1",
			"zZ_9",
			"9_Fg",
			]

		for username in usernames:
			response = self.client.post("/request_profile/", {
					"username": username,
					"first_name": "first",
					"last_name": "last",
					"email": "request@email.com",
					"affiliation_with_the_house": UserProfile.RESIDENT,
					"password": "pwd",
					"confirm_password": "pwd",
					}, follow=True)
			self.assertRedirects(response, reverse("external"))

	def test_duplicate_request(self):
		u = User.objects.create_user(username="u", password="pwd")
		u.save()

		response = self.client.post("/request_profile/", {
				"username": "u",
				"first_name": "first",
				"last_name": "last",
				"email": "request@email.com",
				"affiliation_with_the_house": UserProfile.RESIDENT,
				"password": "pwd",
				"confirm_password": "pwd",
				}, follow=True)
		self.assertIn("This usename is taken.  Try one of u_1 through u_10.",
			      response.content)
		self.assertEqual(response.status_code, 200)

	def test_bad_profile_requests(self):
		response = self.client.post("/request_profile/", {
				"username": "request",
				"first_name": "first",
				"last_name": "last",
				"email": "request@email.com",
				"affiliation_with_the_house": UserProfile.RESIDENT,
				"password": "pwd",
				"confirm_password": "pwd2",
				}, follow=True)
		self.assertEqual(response.status_code, 200)
		self.assertIn("Passwords don&#39;t match.", response.content)

		response = self.client.post("/request_profile/", {
				"username": "request",
				"last_name": "last",
				"email": "request@email.com",
				"affiliation_with_the_house": UserProfile.RESIDENT,
				"password": "pwd",
				"confirm_password": "pwd2",
				}, follow=True)
		self.assertEqual(response.status_code, 200)
		self.assertIn("This field is required.", response.content)

		response = self.client.post("/request_profile/", {
				"username": "*******", # hunter2
				"first_name": "first",
				"last_name": "last",
				"email": "request@email.com",
				"affiliation_with_the_house": UserProfile.RESIDENT,
				"password": "pwd",
				"confirm_password": "pwd2",
				}, follow=True)
		self.assertEqual(response.status_code, 200)
		self.assertIn("Invalid username. Must be characters A-Z, a-z, 0-9, or &quot;_&quot;",
			      response.content)

		response = self.client.post("/request_profile/", {
				"username": "request",
				"first_name": "first",
				"last_name": "last",
				"email": "request@email.com",
				"affiliation_with_the_house": "123",
				"password": "pwd",
				"confirm_password": "pwd",
				}, follow=True)
		self.assertEqual(response.status_code, 200)
		self.assertIn("Select a valid choice. 123 is not one of the available choices.",
			      response.content)

class TestSocialRequest(TestCase):
	def setUp(self):
		self.su = User.objects.create_user(username="su", password="pwd")
		self.su.is_staff, self.su.is_superuser = True, True
		self.su.save()

		self.pr = ProfileRequest(username="pr", email="pr@email.com",
					 affiliation=UserProfile.RESIDENT,
					 provider="github", uid="1234567890")
		self.pr.save()

	def test_profile_request_view(self):
		self.client.login(username="su", password="pwd")

		response = self.client.get("/custom_admin/profile_requests/{0}/"
					   .format(self.pr.pk))
		self.assertEqual(response.status_code, 200)
		self.assertIn(self.pr.email, response.content)

	def test_approve_profile_request(self):
		self.client.login(username="su", password="pwd")

		username = self.pr.username

		response = self.client.post("/custom_admin/profile_requests/{0}/"
					    .format(self.pr.pk), {
				"username": username,
				"first_name": "first",
				"last_name": "last",
				"email": self.pr.email,
				"phone_number": "",
				"status": self.pr.affiliation,
				"current_room": "",
				"former_rooms": "",
				"former_houses": "",
				"is_active": "on",
				"add_user": "",
				}, follow=True)

		self.assertRedirects(response, "/custom_admin/profile_requests/")
		self.assertIn("User {0} was successfully added".format(username),
			      response.content)

class TestProfilePages(TestCase):
	def setUp(self):
		self.u = User.objects.create_user(username="u", email="u@email.com", password="pwd")
		self.u.save()

		self.profile = UserProfile.objects.get(user=self.u)
		self.profile.current_room = "Test Current Room"
		self.profile.former_rooms = "Test Former Room, Test Formerer Room"
		self.profile.former_houses = "Test House, Test Houser, Test Housest"
		self.profile.phone_number = "(111) 111-111"
		self.profile.email_visible = True
		self.profile.phone_visible = True
		self.profile.status = UserProfile.RESIDENT
		self.profile.save()

		self.client.login(username="u", password="pwd")

	def test_profile_pages(self):
		urls = [
			"/profile/",
			"/profile/{0}/".format(self.u.username),
			]
		for url in urls:
			response = self.client.get(url)
			print url
			print response.content
			self.assertIn(self.u.username, response.content)
			self.assertIn(self.profile.current_room, response.content)
			self.assertIn(self.profile.former_rooms, response.content)
			self.assertIn(self.profile.former_houses, response.content)
			self.assertIn(self.profile.phone_number, response.content)
			# self.assertIn(UserProfile.STATUS_CHOICES[0][1], response.content)

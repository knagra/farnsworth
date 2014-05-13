"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from datetime import datetime, timedelta
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils.timezone import utc
from threads.models import UserProfile, Thread, Message
from managers.models import Manager, Announcement, RequestType, Request
from events.models import Event

class VerifyUser(TestCase):
	def setUp(self):
		self.u = User.objects.create_user(username="u", email="u@email.com", password="pwd")
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

class VerifyThread(TestCase):
	def setUp(self):
		self.u = User.objects.create_user(username="u", email="u@email.com", password="pwd")
		self.u.save()
		profile = UserProfile.objects.get(user=self.u)
		self.thread = Thread(owner=profile, subject="Default Thread Test")
		self.thread.save()
		self.client.login(username="u", password="pwd")

	def test_thread_created(self):
		self.assertEqual(1, Thread.objects.all().count())
		self.assertEqual(self.thread, Thread.objects.get(pk=self.thread.pk))
		self.assertEqual(1, Thread.objects.filter(subject=self.thread.subject).count())
		self.assertEqual(0, Thread.objects.filter(subject="Tabboo").count())

	def test_thread_created(self):
		urls = [
			"/",
			"/thread/{0}/".format(self.thread.pk),
			"/archives/list_all_threads/",
			"/member_forums/",
			"/archives/all_threads/",
			]
			
		for url in urls:
			response = self.client.get(url)
			self.assertEqual(response.status_code, 200)
			self.assertIn(self.thread.subject, response.content)

	def test_create_thread(self):
		urls = [
			"/my_threads/",
			"/member_forums/",
			"/archives/all_threads/",
			]
		for url in urls:
			response = self.client.post(url, {
					"submit_thread_form": "",
					"subject": "Thread Subject Test",
					"body": "Thread Body Test",
					}, follow=True)
			self.assertRedirects(response, url)
			self.assertIn("Thread Subject Test", response.content)
			self.assertIn("Thread Body Test", response.content)

			Thread.objects.get(subject="Thread Subject Test").delete()

	def test_post_reply(self):
		urls = [
			"/member_forums/",
			"/thread/{0}/".format(self.thread.pk),
			"/archives/all_threads/",
			]

		for url in urls:
			response = self.client.post(url, {
					"submit_message_form": "",
					"thread_pk": "{0}".format(self.thread.pk),
					"body": "Message Body Test",
					}, follow=True)
			self.assertRedirects(response, url)
			self.assertIn("Message Body Test", response.content)

			Message.objects.all()[0].delete()
			self.assertEqual(0, Message.objects.all().count())

class FromHome(TestCase):
	def setUp(self):
		self.u = User.objects.create_user(username="u", email="u@email.com", password="pwd")
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

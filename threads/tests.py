"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".
"""

from datetime import datetime, timedelta
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils.timezone import utc
from base.models import UserProfile
from threads.models import Thread, Message
from managers.models import Manager, Announcement, RequestType, Request
from events.models import Event

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

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

from events.models import Event

class TestEvent(TestCase):
	def setUp(self):
		self.u = User.objects.create_user(username="u", email="u@email.com", password="pwd")
		self.u.save()

		profile = UserProfile.objects.get(user=self.u)
		now = datetime.utcnow().replace(tzinfo=utc)
		one_day = timedelta(days=1)

		self.ev = Event(owner=profile, title="Event Title Test",
				description="Event Description Test",
				start_time=now, end_time=now + one_day)
		self.ev.save()

		self.client.login(username="u", password="pwd")

	def test_event_views(self):
		urls = [
			"/events/",
			"/archives/all_events/",
			]
		for url in urls:
			response = self.client.get(url)
			self.assertEqual(response.status_code, 200)
			self.assertIn(self.ev.title, response.content)
			self.assertIn(self.ev.description, response.content)

	def test_rsvp(self):
		urls = [
			"/events/",
			"/archives/all_events/",
			]
		for url in urls:
			response = self.client.post(url, {
					"rsvp": "",
					"event_pk": "{0}".format(self.ev.pk),
					}, follow=True)
			self.assertRedirects(response, url)
			self.assertIn('title="Un-RSVP"', response.content)

			response = self.client.post(url, {
					"rsvp": "",
					"event_pk": "{0}".format(self.ev.pk),
					}, follow=True)
			self.assertRedirects(response, url)
			self.assertIn('title="RSVP"', response.content)

	def test_edit(self):
		response = self.client.post("/edit_event/{0}/".format(self.ev.pk), {
				"title": "New Title Test",
				"description": self.ev.description,
				"location": self.ev.location,
				"start_time": self.ev.start_time.strftime("%m/%d/%Y %R %p"),
				"end_time": self.ev.end_time.strftime("%m/%d/%Y %R %p"),
				"as_manager": "",
				}, follow=True)
		self.assertIn("New Title Test", response.content)
		self.assertRedirects(response, "/events/")

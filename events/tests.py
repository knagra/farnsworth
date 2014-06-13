"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from datetime import datetime, timedelta
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils.timezone import utc

from utils.variables import time_formats, MESSAGES
from base.models import UserProfile
from threads.models import Thread, Message
from events.models import Event

class TestEvent(TestCase):
	def setUp(self):
		self.u = User.objects.create_user(username="u", password="pwd")
		self.ou = User.objects.create_user(username="ou", password="pwd")
		self.su = User.objects.create_user(username="su", password="pwd")

		self.su.is_staff, self.su.is_superuser = True, True
		self.su.save()

		self.profile = UserProfile.objects.get(user=self.u)
		now = datetime.utcnow().replace(tzinfo=utc)
		one_day = timedelta(days=1)

		self.ev = Event(
			owner=self.profile,
			title="Event Title Test",
			description="Event Description Test",
			start_time=now, end_time=now + one_day,
			)
		self.ev.save()

		self.client.login(username="u", password="pwd")

	def test_event_views(self):
		urls = [
			"/events/",
			"/events/{0}/".format(self.ev.pk),
			"/events/all/",
			]
		for url in urls:
			response = self.client.get(url)
			self.assertEqual(response.status_code, 200)
			self.assertContains(response, self.ev.title)
			self.assertContains(response, self.ev.description)

	def test_rsvp(self):
		urls = [
			"/events/",
			"/events/{0}/".format(self.ev.pk),
			"/events/all/",
			]
		for url in urls:
			response = self.client.post(url, {
					"rsvp": "",
					"event_pk": "{0}".format(self.ev.pk),
					}, follow=True)
			self.assertRedirects(response, url)
			self.assertContains(response, 'Un-RSVP')
			self.assertContains(response,
								MESSAGES['RSVP_ADD'].format(event=self.ev.title))

			self.assertEqual(1, self.ev.rsvps.count())
			self.assertEqual(self.profile, self.ev.rsvps.all()[0])

			response = self.client.post(url, {
					"rsvp": "",
					"event_pk": "{0}".format(self.ev.pk),
					}, follow=True)
			self.assertRedirects(response, url)
			self.assertContains(response, 'RSVP')
			self.assertContains(response,
								MESSAGES['RSVP_REMOVE'].format(event=self.ev.title))

			self.assertEqual(0, self.ev.rsvps.count())

	def test_edit(self):
		response = self.client.post("/events/{0}/edit/".format(self.ev.pk), {
				"title": "New Title Test",
				"description": self.ev.description,
				"location": self.ev.location,
				"start_time": self.ev.start_time.strftime(time_formats[0]),
				"end_time": self.ev.end_time.strftime(time_formats[0]),
				"as_manager": "",
				}, follow=True)
		self.assertContains(response, "New Title Test")
		self.assertRedirects(response, "/events/{0}/".format(self.ev.pk))

	def test_no_edit(self):
		self.client.logout()
		self.client.login(username="ou", password="pwd")

		response = self.client.get("/events/{0}/edit/".format(self.ev.pk))
		self.assertRedirects(response, "/events/{0}/".format(self.ev.pk))

		self.client.logout()
		self.client.login(username="su", password="pwd")

		response = self.client.get("/events/{0}/edit/".format(self.ev.pk))
		self.assertEqual(response.status_code, 200)

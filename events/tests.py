"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".
"""

from datetime import timedelta

from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.http import QueryDict
from django.test import TestCase
from django.utils.timezone import now, utc

import pytz

from utils.variables import time_formats, MESSAGES
from base.models import UserProfile
from events.models import Event
from events.forms import RsvpForm
from managers.models import Manager

class TestEvent(TestCase):
    def setUp(self):
        self.u = User.objects.create_user(username="u", password="pwd")
        self.ou = User.objects.create_user(username="ou", password="pwd")
        self.su = User.objects.create_user(username="su", password="pwd")

        self.su.is_staff, self.su.is_superuser = True, True
        self.su.save()

        self.profile = UserProfile.objects.get(user=self.u)
        start = now().replace(second=0, microsecond=0)
        one_day = timedelta(days=1)

        self.ev = Event.objects.create(
            owner=self.profile,
            title="Event Title Test",
            location="Development Land",
            description="Event Description Test",
            start_time=start,
            end_time=start + one_day,
            )

        self.m = Manager.objects.create(
            title="Event Manager",
            incumbent=self.profile,
            )

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
                "rsvp-{0}".format(self.ev.pk): "",
                }, follow=True)
            self.assertRedirects(response, url)
            self.assertContains(response, 'Un-RSVP')
            self.assertContains(
                response,
                MESSAGES['RSVP_ADD'].format(event=self.ev.title),
                )

            self.assertEqual(1, self.ev.rsvps.count())
            self.assertEqual(self.profile, self.ev.rsvps.all()[0])

            response = self.client.post(url, {
                "rsvp": "",
                "rsvp-{0}".format(self.ev.pk): "",
                }, follow=True)
            self.assertRedirects(response, url)
            self.assertContains(response, 'RSVP')
            self.assertContains(
                response,
                MESSAGES['RSVP_REMOVE'].format(event=self.ev.title),
                )

            self.assertEqual(0, self.ev.rsvps.count())

    def test_edit(self):
        if settings.USE_TZ:
            tz = pytz.timezone(settings.TIME_ZONE)
            start = tz.normalize(self.ev.start_time)
            end = tz.normalize(self.ev.end_time)
        else:
            start = self.ev.start_time
            end = self.ev.end_time
        response = self.client.post("/events/{0}/edit/".format(self.ev.pk), {
            "title": "New Title Test",
            "description": self.ev.description,
            "location": self.ev.location,
            "start_time": start.strftime(time_formats[0]),
            "end_time": end.strftime(time_formats[0]),
            "as_manager": self.m.pk,
            "cancelled": "on",
            }, follow=True)
        self.assertContains(response, "New Title Test")
        self.assertRedirects(response, "/events/{0}/".format(self.ev.pk))
        event = Event.objects.get(pk=self.ev.pk)
        self.assertEqual(event.title, "New Title Test")
        self.assertEqual(event.description, self.ev.description)
        self.assertEqual(event.location, self.ev.location)
        self.assertEqual(
            self.ev.start_time,
            event.start_time,
            )
        self.assertEqual(
            self.ev.end_time,
            event.end_time,
            )
        self.assertEqual(event.cancelled, True)
        self.assertEqual(event.as_manager, self.m)

    def test_add_event(self):
        if settings.USE_TZ:
            tz = pytz.timezone(settings.TIME_ZONE)
            start = tz.normalize(self.ev.start_time)
            end = tz.normalize(self.ev.end_time)
        else:
            start = self.ev.start_time
            end = self.ev.end_time

        urls = [
            "/events/",
            "/events/all/",
            ]

        for url in urls:
            response = self.client.post(url, {
                "post_event": "",
                "title": "New Event Title",
                "description": "New Description",
                "location": "New Location Hall",
                "start_time": start.strftime(time_formats[0]),
                "end_time": end.strftime(time_formats[0]),
                "as_manager": self.m.pk,
                }, follow=True)
            self.assertRedirects(response, url)
            event = Event.objects.get(pk=self.ev.pk + 1)
            self.assertEqual(event.title, "New Event Title")
            self.assertEqual(event.description, "New Description")
            self.assertEqual(event.location, "New Location Hall")
            self.assertEqual(
                self.ev.start_time,
                event.start_time,
                )
            self.assertEqual(
                self.ev.end_time,
                event.end_time,
                )
            self.assertEqual(event.as_manager, self.m)

    def test_bad_time(self):
        urls = [
            "/events/",
            "/events/all/",
            ]
        for url in urls:
            response = self.client.post(url, {
                "post_event": "",
                "title": "New Event Title",
                "description": "New Description",
                "location": "New Location Hall",
                "start_time": self.ev.start_time.strftime(time_formats[0]),
                "end_time": (self.ev.start_time - timedelta(minutes=1)) .strftime(time_formats[0]),
                "as_manager": self.m.pk,
                })
            self.assertEqual(response.status_code, 200)
            self.assertContains(
                response,
                "Start time is later than end time. Unless this event "
                "involves time travel, please change the start or end time.",
                )
            self.assertContains(response, MESSAGES['EVENT_ERROR'])
            self.assertEqual(Event.objects.count(), 1)

    def test_rsvp_already_past(self):
        self.ev.end_time = now() - timedelta(days=1)
        self.ev.save()

        form = RsvpForm(
            QueryDict(""),
            profile=self.profile,
            instance=self.ev,
            )
        self.assertRaises(
            forms.ValidationError,
            form.clean,
            )

    def test_no_edit(self):
        self.client.logout()
        self.client.login(username="ou", password="pwd")

        response = self.client.get("/events/{0}/edit/".format(self.ev.pk))
        self.assertRedirects(response, "/events/{0}/".format(self.ev.pk))

        self.client.logout()
        self.client.login(username="su", password="pwd")

        response = self.client.get("/events/{0}/edit/".format(self.ev.pk))
        self.assertEqual(response.status_code, 200)

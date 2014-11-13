"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from utils.variables import MESSAGES
from base.models import UserProfile
from threads.models import Thread, Message

class VerifyThread(TestCase):
    def setUp(self):
        self.u = User.objects.create_user(username="u", password="pwd")

        self.profile = UserProfile.objects.get(user=self.u)

        self.thread = Thread.objects.create(
            owner=self.profile,
            subject="Default Thread Test",
            )

        self.message = Message.objects.create(
            owner=self.profile,
            body="Default Reply Test",
            thread=self.thread,
            )

        self.client.login(username="u", password="pwd")

    def test_thread_created(self):
        self.assertEqual(1, Thread.objects.all().count())
        self.assertEqual(self.thread, Thread.objects.get(pk=self.thread.pk))
        self.assertEqual(1, Thread.objects.filter(subject=self.thread.subject).count())
        self.assertEqual(0, Thread.objects.filter(subject="Tabboo").count())

    def test_thread_created(self):
        urls = [
            reverse("homepage"),
            reverse("threads:list_all_threads"),
            reverse("threads:view_thread", kwargs={"pk": self.thread.pk}),
            reverse("threads:list_user_threads", kwargs={"targetUsername": self.u.username}),
            reverse("threads:list_user_messages", kwargs={"targetUsername": self.u.username}),
            ]

        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, self.thread.subject)
            self.assertNotContains(response, MESSAGES['MESSAGE_ERROR'])

    def test_create_thread(self):
        subject = "Thread Subject Test"
        body = "Thread Body Test"

        url = reverse("threads:list_all_threads")
        response = self.client.post(url, {
            "submit_thread_form": "",
            "subject": subject,
            "body": body,
            }, follow=True)

        thread = Thread.objects.get(subject=subject)

        self.assertNotEqual(thread, None)
        self.assertEqual(Message.objects.filter(thread=thread).count(), 1)
        self.assertEqual(Message.objects.get(thread=thread).body, body)

        url = reverse("threads:view_thread", kwargs={"pk": thread.pk})
        self.assertRedirects(response, url)
        self.assertContains(response, subject)
        self.assertContains(response, body)

    def test_bad_thread(self):
        urls = [
            reverse("threads:list_all_threads"),
            ]
        subject = "Thread Subject Test"
        body = "Thread Body Test"
        for url in urls:
            response = self.client.post(url, {
                    "submit_thread_form": "",
                    "subject": subject,
                    })
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, MESSAGES['THREAD_ERROR'])
            self.assertEqual(Thread.objects.filter().count(), 1)

            try:
                thread = Thread.objects.get(subject=subject)
            except Thread.DoesNotExist:
                pass
            else:
                self.assertEqual(thread, None)

    def test_post_reply(self):
        urls = [
            reverse("threads:view_thread", kwargs={"pk": self.thread.pk}),
            ]
        body = "Reply Body Test"
        for url in urls:
            response = self.client.post(url, {
                "add_message": "",
                "body": body,
                }, follow=True)

            thread = Thread.objects.get(pk=self.thread.pk)

            self.assertNotEqual(thread, None)
            self.assertEqual(Message.objects.filter(thread=thread).count(), 2)

            url = reverse("threads:view_thread", kwargs={"pk": thread.pk})
            self.assertRedirects(response, url)
            self.assertContains(response, body)

            message = Message.objects.get(thread=thread, body=body)

            self.assertNotEqual(message, None)

            message.delete()

    def test_bad_reply(self):
        urls = [
            reverse("threads:view_thread", kwargs={"pk": self.thread.pk}),
            ]
        body = "Reply Body Test"
        for url in urls:
            response = self.client.post(url, {
                "add_message": "",
                "body": "",
                })
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, MESSAGES['MESSAGE_ERROR'])

            thread = Thread.objects.get(pk=self.thread.pk)

            self.assertNotEqual(thread, None)
            self.assertEqual(Message.objects.filter(thread=thread).count(), 1)

            try:
                message = Message.objects.get(thread=thread, body=body)
            except Message.DoesNotExist:
                pass
            else:
                self.assertEqual(message, None)

    def test_delete_message(self):
        url = reverse("threads:view_thread", kwargs={"pk": self.thread.pk})
        response = self.client.post(url, {
            "delete_message-{0}".format(self.message.pk): "",
            }, follow=True)
        self.assertRedirects(response, reverse("threads:list_all_threads"))
        self.assertEqual(
            0,
            Message.objects.filter(pk=self.message.pk).count(),
            )
        self.assertEqual(
            0,
            Thread.objects.filter(pk=self.thread.pk).count(),
            )

    def test_edit_message(self):
        url = reverse("threads:view_thread", kwargs={"pk": self.thread.pk})
        response = self.client.post(url, {
            "edit_message-{0}".format(self.message.pk): "",
            "edit-{0}-body".format(self.message.pk): "New message body",
            }, follow=True)
        self.assertRedirects(response, url)
        self.assertEqual(
            1,
            Message.objects.filter(pk=self.message.pk).count(),
            )
        self.assertEqual(
            "New message body",
            Message.objects.get(pk=self.message.pk).body
            )

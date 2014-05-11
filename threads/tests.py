"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from datetime import datetime
from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User
from threads.models import UserProfile, Thread

class SimpleTest(TestCase):
	def test_basic_addition(self):
		"""
		Tests that 1 + 1 always equals 2.
		"""
		self.assertEqual(1 + 1, 2)

class VerifyUser(TestCase):
	def setUp(self):
		self.u = User.objects.create_user(username="u", email="u@email.com", password="password")
		self.st = User.objects.create_user(username="st", email="st@email.com", password="password")
		self.su = User.objects.create_user(username="su", email="su@email.com", password="password")
		self.st.is_staff = True
		self.su.is_staff, self.su.is_superuser = True, True
		self.u.save()
		self.st.save()
		self.su.save()

	def test_user_profile_created(self):
		''' Test that the user profile for a user is automatically created when a user is created. '''
		self.assertEqual(1, UserProfile.objects.filter(user=self.u).count())
		self.assertEqual(self.u, UserProfile.objects.get(user=self.u).user)

	def test_login(self):
		self.assertEqual(True, self.client.login(username="u", password="password"))
		self.assertEqual(None, self.client.logout())

	def test_homepage(self):
		response = self.client.get("/")
		self.assertRedirects(response, "/landing/", status_code=302,
				     target_status_code=200)
		self.client.login(username="u", password="password")
		response = self.client.get("/")
		self.assertEqual(response.status_code, 200)
		self.client.logout()
		response = self.client.get("/")
		self.assertRedirects(response, "/landing/", status_code=302,
				     target_status_code=200)

	def test_manage_users(self):
		self.client.login(username="u", password="password")
		response = self.client.get("/custom_admin/manage_users/")
		self.assertRedirects(response, "/", status_code=302, target_status_code=200)
		self.client.logout()
		self.client.login(username="st", password="password")
		response = self.client.get("/custom_admin/manage_users/")
		self.assertRedirects(response, "/", status_code=302, target_status_code=200)
		self.client.logout()
		self.client.login(username="su", password="password")
		response = self.client.get("/custom_admin/manage_users/")
		self.assertEqual(response.status_code, 200)
		self.client.logout()

class VerifyThread(TestCase):
	def setUp(self):
		self.u = User.objects.create_user(username="u", email="u@email.com", password="password")
		self.u.save()
		now = datetime.now()
		profile = UserProfile.objects.get(user=self.u)
		self.thread = Thread(owner=profile, subject="subject")
		self.thread.save()

	def test_thread_created(self):
		self.assertEqual(1, Thread.objects.all().count())
		self.assertEqual(self.thread, Thread.objects.get(pk=self.thread.pk))
		self.assertEqual(1, Thread.objects.filter(subject="subject").count())

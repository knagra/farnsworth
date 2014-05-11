"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from datetime import datetime
from django.test import TestCase
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
		self.user = User.objects.create_user(username="user", email="fake@email.com", first_name="john", last_name="doe", password="password")
		self.user.save()

	def test_user_profile_created(self):
		''' Test that the user profile for a user is automatically created when a user is created. '''
		self.assertEqual(1, UserProfile.objects.filter(user=self.user).count())
		self.assertEqual(self.user, UserProfile.objects.get(user=self.user).user)

class VerifyThread(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username="user", email="fake@email.com", first_name="john", last_name="doe", password="password")
		self.user.save()
		now = datetime.now()
		profile = UserProfile.objects.get(user=self.user)
		self.thread = Thread(owner=profile, subject="subject")
		self.thread.save()

	def test_thread_created(self):
		self.assertEqual(1, Thread.objects.all().count())
		self.assertEqual(self.thread, Thread.objects.get(pk=self.thread.pk))
		self.assertNotEqual(0, Thread.objects.filter(subject="subject").count())

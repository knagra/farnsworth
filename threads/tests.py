"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from models import UserProfile

class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)

class VerifyUser(TestCase):
	def test_user_profile_created(self):
		''' Test that the user profile for a user is automatically created when a user is created. '''
		new_user = User.objects.create_user(username="user", email="fake@email.com", first_name="john", last_name="doe", password="password")
		new_user.save()
		self.assertNotEqual(0, UserProfile.objects.filter(user=new_user).count())
		self.assertEqual(new_user, UserProfile.objects.get(user=new_user).user)

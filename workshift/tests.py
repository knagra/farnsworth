
from django.test import TestCase

from utils.funcs import convert_to_url
from base.models import User, UserProfile
from managers.models import Manager
from workshift.models import Semester

class BasicTest(TestCase):
	def setUp(self):
		self.su = User.objects.create_user(username="su", password="pwd")
		self.su.is_staff, self.su.is_superuser = True, True
		self.su.save()

		self.m = Manager(
			title="Workshift Manager",
			incumbent=UserProfile.objects.get(user=self.su),
			)
		self.m.url_title = convert_to_url(self.m.title)
		self.m.workshift_manager = True
		self.m.save()

		self.sem = Semester(year=2014)
		self.sem.save()

		self.assertTrue(self.client.login(username="su", password="pwd"))

	def test_views(self):
		urls = [
			"/workshift/start/"
			"/workshift/"
			]
		for url in urls:
			response = self.client.get(url)
			self.assertEqual(response.status_code, 200)

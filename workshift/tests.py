
from django.test import TestCase

from datetime import date, timedelta

from utils.funcs import convert_to_url
from base.models import User, UserProfile
from managers.models import Manager
from workshift.models import Semester, WorkshiftProfile

class BasicTest(TestCase):
	def setUp(self):
		self.su = User.objects.create_user(username="su", password="pwd")
		self.su.is_staff, self.su.is_superuser = True, True
		self.su.first_name, self.su.last_name = "Super", "User"
		self.su.save()

		self.m = Manager(
			title="Workshift Manager",
			incumbent=UserProfile.objects.get(user=self.su),
			)
		self.m.url_title = convert_to_url(self.m.title)
		self.m.workshift_manager = True
		self.m.save()

		self.sem = Semester(year=2014, start_date=date.today(),
							end_date=date.today() + timedelta(days=7),
							current=True)
		self.sem.save()

		self.wprofile = WorkshiftProfile(user=self.su, semester=self.sem)
		self.wprofile.save()

		self.assertTrue(self.client.login(username="su", password="pwd"))

	def test_views(self):
		urls = [
			"/workshift/start/",
			"/workshift/",
			"/workshift/{0}{1}/".format(self.sem.season, self.sem.year),
			"/workshift/manage/",
			"/workshift/manage/assign_shifts/",
			"/workshift/add_shift/",
			"/workshift/types/",
			]
		for url in urls:
			response = self.client.get(url)
			self.assertEqual(response.status_code, 200)

			response = self.client.get(url[:-1])
			self.assertEqual(response.status_code, 200)

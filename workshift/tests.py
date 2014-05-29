
from django.test import TestCase

from datetime import date, timedelta, datetime

from utils.variables import DAYS
from utils.funcs import convert_to_url
from base.models import User, UserProfile
from managers.models import Manager
from workshift.models import Semester, WorkshiftPool, WorkshiftProfile, \
	 WorkshiftType, RegularWorkshift, WorkshiftInstance, OneTimeWorkshift, \
	 ShiftLogEntry

class BasicTest(TestCase):
	"""
	Tests a few basic things about the application: That all the pages can load
	correctly, and that they contain the content that is expected.
	"""
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

		self.pool = WorkshiftPool(
			semester=self.sem,
			)
		self.pool.save()

		self.wprofile = WorkshiftProfile(user=self.su, semester=self.sem)
		self.wprofile.save()

		self.wtype = WorkshiftType(title="Test Posts")
		self.wtype.save()

		self.shift = RegularWorkshift(
			workshift_type=self.wtype,
			pool=self.pool,
			title="Test Regular Shift",
			day=DAYS[0][0],
			start_time=datetime.now(),
			end_time=datetime.now() + timedelta(hours=2),
			)
		self.shift.save()

		self.instance = WorkshiftInstance(
			weekly_workshift=self.shift,
			pool=self.pool,
			date=date.today(),
			workshifter=self.wprofile,
			)
		self.instance.save()

		self.once = OneTimeWorkshift(
			title="Test One Time Shift",
			pool=self.pool,
			description="One Time Description",
			date=date.today(),
			workshifter=self.wprofile,
			)
		self.once.save()

		self.sle0 = ShiftLogEntry(
			person=self.wprofile,
			note="Test Shift Log #0",
			entry_type=ShiftLogEntry.ASSIGNED,
			)

		self.sle1 = ShiftLogEntry(
			person=self.wprofile,
			note="Test Shift Log #1",
			entry_type=ShiftLogEntry.SIGNOUT,
			)

		self.sle2 = ShiftLogEntry(
			person=self.wprofile,
			note="Test Shift Log #2",
			entry_type=ShiftLogEntry.SIGNIN,
			)

		self.sle3 = ShiftLogEntry(
			person=self.wprofile,
			note="Test Shift Log #3",
			entry_type=ShiftLogEntry.VERIFY,
			)

		self.sle0.save()
		self.sle1.save()
		self.sle2.save()
		self.sle3.save()

		self.instance.shift_log = [self.sle0, self.sle1, self.sle2, self.sle3]
		self.once.shift_log = [self.sle0, self.sle1, self.sle2, self.sle3]

		self.instance.save()
		self.once.save()

		self.assertTrue(self.client.login(username="su", password="pwd"))

	def test_views(self):
		urls = [
			"/start/",
			"/add_shift/",
			"/types/",
			"/type/{0}/".format(self.wtype.pk),
			"/type/{0}/edit/".format(self.wtype.pk),
			]
		for url in urls:
			response = self.client.get("/workshift" + url)
			self.assertEqual(response.status_code, 200)

			response = self.client.get("/workshift" + url[:-1])
			self.assertEqual(response.status_code, 200)

		urls = [
			"/",
			"/profile/{0}/".format(self.wprofile.pk),
			"/profile/{0}/preferences/".format(self.wprofile.pk),
			"/manage/",
			"/manage/assign_shifts/",
			"/shift/{0}/".format(self.shift.pk),
			"/shift/{0}/edit/".format(self.shift.pk),
			"/instance/{0}/".format(self.instance.pk),
			"/instance/{0}/edit/".format(self.instance.pk),
			"/once/{0}/".format(self.once.pk),
			"/once/{0}/edit/".format(self.once.pk),
			]
		for url in urls:
			response = self.client.get("/workshift" + url)
			self.assertEqual(response.status_code, 200)

			response = self.client.get("/workshift" + url[:-1])
			self.assertEqual(response.status_code, 200)

			prefix = "/workshift/{0}{1}".format(self.sem.season, self.sem.year)
			response = self.client.get(prefix + url)
			self.assertEqual(response.status_code, 200)

			response = self.client.get(prefix + url[:-1])
			self.assertEqual(response.status_code, 200)

	def test_type(self):
		response = self.client.get("/workshift/types/")
		self.assertEqual(response.status_code, 200)
		self.assertIn(self.wtype.title, response.content)
		self.assertIn(self.wtype.hours, response.content)
		self.assertNotIn(self.wtype.quick_tips, response.content)
		self.assertNotIn(self.wtype.description, response.content)

		response = self.client.get("/workshift/type/{0}/".format(self.wtype.pk))
		self.assertEqual(response.status_code, 200)
		self.assertIn(self.wtype.title, response.content)
		self.assertIn(self.wtype.hours, response.content)
		self.assertIn(self.wtype.quick_tips, response.content)
		self.assertIn(self.wtype.description, response.content)

		response = self.client.get("/workshift/type/{0}/edit/".format(self.wtype.pk))
		self.assertEqual(response.status_code, 200)
		self.assertIn(self.wtype.title, response.content)
		self.assertIn(self.wtype.hours, response.content)
		self.assertIn(self.wtype.quick_tips, response.content)
		self.assertIn(self.wtype.description, response.content)

	def test_shift(self):
		response = self.client.get("/workshift/shift/{0}/".format(self.shift.pk))
		self.assertEqual(response.status_code, 200)
		self.assertIn(self.shift.title, response.content)
		self.assertIn(self.shift.hours, response.content)
		self.assertIn(self.shift.quick_tips, response.content)
		self.assertIn(self.shift.description, response.content)
		self.assertIn(self.shift.current_assignee.user.get_full_name(), response.content)

		response = self.client.get("/workshift/shift/{0}/edit/".format(self.shift.pk))
		self.assertEqual(response.status_code, 200)
		self.assertIn(self.shift.title, response.content)
		self.assertIn(self.shift.hours, response.content)
		self.assertIn(self.shift.quick_tips, response.content)
		self.assertIn(self.shift.description, response.content)
		self.assertIn(self.shift.current_assignee.user.get_full_name(), response.content)

	def test_instance(self):
		response = self.client.get("/workshift/instance/{0}/".format(self.instance.pk))
		self.assertEqual(response.status_code, 200)
		self.assertIn(self.instance.weekly_workshift.title, response.content)
		self.assertIn(self.instance.pool.title, response.content)
		self.assertIn(self.instance.date, response.content)
		self.assertIn(self.instance.workshifter.user.get_full_name(), response.content)
		self.assertIn(self.instance.hours, response.content)
		self.assertIn(self.sle0.note, response.content)
		self.assertIn(self.sle1.note, response.content)
		self.assertIn(self.sle2.note, response.content)
		self.assertIn(self.sle3.note, response.content)

		response = self.client.get("/workshift/instance/{0}/edit/".format(self.instance.pk))
		self.assertEqual(response.status_code, 200)
		self.assertIn(self.instance.weekly_workshift.title, response.content)
		self.assertIn(self.instance.pool.title, response.content)
		self.assertIn(self.instance.date, response.content)
		self.assertIn(self.instance.workshifter.user.get_full_name(), response.content)
		self.assertIn(self.instance.hours, response.content)

	def test_one_time(self):
		response = self.client.get("/workshift/once/{0}/".format(self.once.pk))
		self.assertEqual(response.status_code, 200)
		self.assertIn(self.once.title, response.content)
		self.assertIn(self.once.pool.title, response.content)
		self.assertIn(self.once.description, response.content)
		self.assertIn(self.once.hours, response.content)
		self.assertIn(self.once.workshifter.user.get_full_name(), response.content)

		response = self.client.get("/workshift/once/{0}/edit/".format(self.once.pk))
		self.assertEqual(response.status_code, 200)
		self.assertIn(self.once.title, response.content)
		self.assertIn(self.once.pool.title, response.content)
		self.assertIn(self.once.description, response.content)
		self.assertIn(self.once.hours, response.content)
		self.assertIn(self.once.workshifter.user.get_full_name(), response.content)

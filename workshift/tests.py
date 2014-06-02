
from django.test import TestCase

from datetime import date, timedelta, datetime

from utils.variables import DAYS, MESSAGES
from utils.funcs import convert_to_url
from base.models import User, UserProfile
from managers.models import Manager
from workshift.models import *
from workshift.forms import *

class TestStart(TestCase):
	def setUp(self):
		self.wu = User.objects.create_user(username="wu", password="pwd")
		self.wu.first_name, self.wu.last_name = "Cooperative", "User"
		self.wu.save()

		self.wm = Manager(
			title="Workshift Manager",
			incumbent=UserProfile.objects.get(user=self.wu),
			workshift_manager=True,
			)
		self.wm.url_title = convert_to_url(self.wm.title)
		self.wm.save()

		self.assertTrue(self.client.login(username="wu", password="pwd"))

	def test_start(self):
		response = self.client.post("/workshift/start/", {
			"season": Semester.SUMMER,
			"year": 2014,
			"rate": 13.30,
			"self_sign_out": "on",
			"policy": "http://bsc.coop",
			"start_date": "05/22/2014",
			"end_date": "08/15/2014",
		}, follow=True)
		self.assertRedirects(response, "/workshift/manage/")

		self.assertEqual(
			Semester.objects.filter(year=2014).filter(season=Semester.SUMMER).count(),
			1,
			)

		semester = Semester.objects.get(year=2014, season=Semester.SUMMER)

		self.assertEqual(
			WorkshiftProfile.objects.filter(semester=semester).count(),
			1,
			)

		profile = WorkshiftProfile.objects.get(semester=semester)

		self.assertEqual(
			WorkshiftPool.objects.filter(semester=semester).count(),
			1,
			)

		pool = WorkshiftPool.objects.get(semester=semester)

		self.assertEqual(PoolHours.objects.filter(pool=pool).count(), 1)

		pool_hours = PoolHours.objects.get(pool=pool)

		self.assertIn(pool_hours, profile.pool_hours.all())

class TestViews(TestCase):
	"""
	Tests a few basic things about the application: That all the pages can load
	correctly, and that they contain the content that is expected.
	"""
	def setUp(self):
		self.wu = User.objects.create_user(username="wu", password="pwd")
		self.wu.first_name, self.wu.last_name = "Cooperative", "User"
		self.wu.save()

		self.wm = Manager(
			title="Workshift Manager",
			incumbent=UserProfile.objects.get(user=self.wu),
			workshift_manager=True,
			)
		self.wm.url_title = convert_to_url(self.wm.title)
		self.wm.save()

		self.sem = Semester(year=2014, start_date=date.today(),
							end_date=date.today() + timedelta(days=7),
							current=True)
		self.sem.save()

		self.pool = WorkshiftPool(
			semester=self.sem,
			)
		self.pool.save()
		self.pool.managers = [self.wm]
		self.pool.save()

		self.wprofile = WorkshiftProfile(user=self.wu, semester=self.sem)
		self.wprofile.save()

		self.wtype = WorkshiftType(
			title="Test Posts",
			description="Test WorkshiftType Description",
			quick_tips="Test Quick Tips",
			)
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
			date=date.today(),
			workshifter=self.wprofile,
			)
		self.instance.save()

		info = InstanceInfo(
			title="Test One Time Shift",
			pool=self.pool,
			description="One Time Description",
			)
		info.save()

		self.once = WorkshiftInstance(
			info=info,
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

		self.sle4 = ShiftLogEntry(
			person=self.wprofile,
			note="Test Shift Log #4",
			entry_type=ShiftLogEntry.BLOWN,
			)

		self.sle0.save()
		self.sle1.save()
		self.sle2.save()
		self.sle3.save()
		self.sle4.save()

		self.instance.shift_log = [self.sle0, self.sle1, self.sle2, self.sle3, self.sle4]
		self.once.shift_log = [self.sle0, self.sle1, self.sle2, self.sle3, self.sle4]

		self.instance.save()
		self.once.save()

		self.assertTrue(self.client.login(username="wu", password="pwd"))

	def test_views_load(self):
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

		urls = [
			"/",
			"/profile/{0}/".format(self.wprofile.pk),
			"/profile/{0}/preferences/".format(self.wprofile.pk),
			"/manage/",
			"/manage/assign_shifts/",
			"/manage/add_workshifter/",
			"/shift/{0}/".format(self.shift.pk),
			"/shift/{0}/edit/".format(self.shift.pk),
			"/instance/{0}/".format(self.instance.pk),
			"/instance/{0}/edit/".format(self.instance.pk),
			"/instance/{0}/".format(self.once.pk),
			"/instance/{0}/edit/".format(self.once.pk),
			]
		for url in urls:
			response = self.client.get("/workshift" + url)
			self.assertEqual(response.status_code, 200)

			prefix = "/workshift/{0}{1}".format(self.sem.season, self.sem.year)
			response = self.client.get(prefix + url)
			self.assertEqual(response.status_code, 200)

	def test_type(self):
		response = self.client.get("/workshift/types/")
		self.assertEqual(response.status_code, 200)
		self.assertIn(self.wtype.title, response.content)
		self.assertIn(str(self.wtype.hours), response.content)
		self.assertNotIn(self.wtype.quick_tips, response.content)
		self.assertNotIn(self.wtype.description, response.content)

		response = self.client.get("/workshift/type/{0}/".format(self.wtype.pk))
		self.assertEqual(response.status_code, 200)
		self.assertIn(self.wtype.title, response.content)
		self.assertIn(str(self.wtype.hours), response.content)
		self.assertIn(self.wtype.quick_tips, response.content)
		self.assertIn(self.wtype.description, response.content)

		response = self.client.get("/workshift/type/{0}/edit/".format(self.wtype.pk))
		self.assertEqual(response.status_code, 200)
		self.assertIn(self.wtype.title, response.content)
		self.assertIn(str(self.wtype.hours), response.content)
		self.assertIn(self.wtype.quick_tips, response.content)
		self.assertIn(self.wtype.description, response.content)

	def test_shift(self):
		response = self.client.get("/workshift/shift/{0}/".format(self.shift.pk))
		self.assertEqual(response.status_code, 200)
		self.assertIn(self.shift.title, response.content)
		self.assertIn(str(self.shift.hours), response.content)
		self.assertIn(self.shift.workshift_type.quick_tips, response.content)
		self.assertIn(self.shift.workshift_type.description, response.content)
		self.assertIn(self.shift.current_assignee.user.get_full_name(), response.content)

		response = self.client.get("/workshift/shift/{0}/edit/".format(self.shift.pk))
		self.assertEqual(response.status_code, 200)
		self.assertIn(self.shift.title, response.content)
		self.assertIn(str(self.shift.hours), response.content)
		self.assertIn(self.shift.workshift_type.quick_tips, response.content)
		self.assertIn(self.shift.workshift_type.description, response.content)
		self.assertIn(self.shift.current_assignee.user.get_full_name(), response.content)

	def test_instance(self):
		response = self.client.get("/workshift/instance/{0}/"
								   .format(self.instance.pk))
		self.assertEqual(response.status_code, 200)
		self.assertIn(self.instance.weekly_workshift.title, response.content)
		self.assertIn(self.instance.weekly_workshift.pool.title, response.content)
		self.assertIn(self.instance.date, response.content)
		self.assertIn(self.instance.workshifter.user.get_full_name(), response.content)
		self.assertIn(str(self.instance.hours), response.content)
		self.assertIn(self.sle0.note, response.content)
		self.assertIn(self.sle1.note, response.content)
		self.assertIn(self.sle2.note, response.content)
		self.assertIn(self.sle3.note, response.content)
		self.assertIn(self.sle4.note, response.content)

		response = self.client.get("/workshift/instance/{0}/edit/"
								   .format(self.instance.pk))
		self.assertEqual(response.status_code, 200)
		self.assertIn(self.instance.weekly_workshift.title, response.content)
		self.assertIn(self.instance.weekly_workshift.pool.title, response.content)
		self.assertIn(self.instance.date, response.content)
		self.assertIn(self.instance.workshifter.user.get_full_name(), response.content)
		self.assertIn(str(self.instance.hours), response.content)

	def test_one_time(self):
		response = self.client.get("/workshift/instance/{0}/".format(self.once.pk))
		self.assertEqual(response.status_code, 200)
		self.assertIn(self.once.title, response.content)
		self.assertIn(self.once.pool.title, response.content)
		self.assertIn(self.once.description, response.content)
		self.assertIn(str(self.once.hours), response.content)
		self.assertIn(self.once.workshifter.user.get_full_name(), response.content)
		self.assertIn(self.sle0.note, response.content)
		self.assertIn(self.sle1.note, response.content)
		self.assertIn(self.sle2.note, response.content)
		self.assertIn(self.sle3.note, response.content)
		self.assertIn(self.sle4.note, response.content)

		response = self.client.get("/workshift/instance/{0}/edit/".format(self.once.pk))
		self.assertEqual(response.status_code, 200)
		self.assertIn(self.once.title, response.content)
		self.assertIn(self.once.pool.title, response.content)
		self.assertIn(self.once.description, response.content)
		self.assertIn(str(self.once.hours), response.content)
		self.assertIn(self.once.workshifter.user.get_full_name(),
					  response.content)

	def test_semester_view(self):
		response = self.client.get("/workshift/")
		self.assertEqual(response.status_code, 200)

		response = self.client.get("/workshift/?day=2014-01-01")
		self.assertEqual(response.status_code, 200)
		self.assertIn("Wednesday, January  1, 2014", response.content)
		self.assertIn("?day=2013-12-31", response.content)
		self.assertIn("?day=2014-01-02", response.content)

class TestInteractForms(TestCase):
	def setUp(self):
		self.wu = User.objects.create_user(username="wu", password="pwd")
		self.u = User.objects.create_user(username="u", password="pwd")
		self.ou = User.objects.create_user(username="ou", password="pwd")

		self.wm = Manager(
			title="Workshift Manager",
			incumbent=UserProfile.objects.get(user=self.wu),
			workshift_manager=True,
			)
		self.wm.url_title = convert_to_url(self.wm.title)
		self.wm.save()

		self.sem = Semester(year=2014, start_date=date.today(),
							end_date=date.today() + timedelta(days=7),
							current=True)
		self.sem.save()

		self.pool = WorkshiftPool(
			semester=self.sem,
			any_blown=True,
			self_verify=True,
			)
		self.pool.save()
		self.pool.managers = [self.wm]
		self.pool.save()

		self.wp = WorkshiftProfile(user=self.wu, semester=self.sem)
		self.up = WorkshiftProfile(user=self.u, semester=self.sem)
		self.op = WorkshiftProfile(user=self.ou, semester=self.sem)

		self.wp.save()
		self.up.save()
		self.op.save()

		ph = PoolHours(pool=self.pool)
		ph.save()

		self.up.pool_hours = [ph]
		self.up.save()

		self.wtype = WorkshiftType(
			title="Test Posts",
			description="Test WorkshiftType Description",
			quick_tips="Test Quick Tips",
			)
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
			date=date.today(),
			workshifter=self.up,
			)
		self.instance.save()

		info = InstanceInfo(
			title="Test One Time Shift",
			pool=self.pool,
			)
		info.save()

		self.once = WorkshiftInstance(
			info=info,
			date=date.today(),
			)
		self.once.save()

		self.sle0 = ShiftLogEntry(
			person=self.wp,
			entry_type=ShiftLogEntry.ASSIGNED,
			)

		self.sle0.save()

		self.instance.shift_log = [self.sle0]
		self.once.shift_log = [self.sle0]

		self.instance.save()
		self.once.save()

	def test_verify(self):
		self.assertTrue(self.client.login(username="u", password="pwd"))

		form = VerifyShiftForm({"pk": self.instance.pk}, profile=self.up)
		self.assertTrue(form.is_valid())
		self.assertEqual(None, form.save())
		log = self.instance.log.filter(entry_type=ShiftLogEntry.VERIFY)
		self.assertEqual(1, log.count())
		self.assertEqual(log[0].person, self.up)

		form = VerifyShiftForm({"pk": self.once.pk}, profile=self.up)
		self.assertFalse(form.is_valid())
		self.assertIn("Workshift is not filled.", form.errors["pk"])

	def test_no_self_verify(self):
		self.pool.self_verify = False
		self.pool.save()

		self.assertTrue(self.client.login(username="u", password="pwd"))

		form = VerifyShiftForm({"pk": self.instance.pk}, profile=self.up)
		self.assertFalse(form.is_valid())
		self.assertIn("Workshifter cannot verify self.", form.errors["pk"])

		self.assertTrue(self.client.login(username="ou", password="pwd"))

		form = VerifyShiftForm({"pk": self.instance.pk}, profile=self.op)
		self.assertTrue(form.is_valid())
		self.assertEqual(None, form.save())
		log = self.instance.log.filter(entry_type=ShiftLogEntry.VERIFY)
		self.assertEqual(1, log.count())
		self.assertEqual(log[0].person, self.op)

	def test_blown(self):
		self.assertTrue(self.client.login(username="ou", password="pwd"))

		form = BlownShiftForm({"pk": self.instance.pk}, profile=self.op)
		self.assertTrue(form.is_valid())
		self.assertEqual(None, form.save())
		log = self.instance.log.filter(entry_type=ShiftLogEntry.BLOWN)
		self.assertEqual(1, log.count())
		self.assertEqual(log[0].person, self.op)

		form = BlownShiftForm({"pk": self.once.pk}, profile=self.op)
		self.assertFalse(form.is_valid())
		self.assertIn("Workshift is not filled.", form.errors["pk"])

	def test_manager_blown(self):
		self.pool.any_blown = False
		self.pool.save()

		self.assertTrue(self.client.login(username="ou", password="pwd"))

		form = BlownShiftForm({"pk": self.instance.pk}, profile=self.op)
		self.assertFalse(form.is_valid())
		self.assertIn("You are not a workshift manager.", form.errors["pk"])

		self.client.logout()

		self.assertTrue(self.client.login(username="wu", password="pwd"))

		form = BlownShiftForm({"pk": self.instance.pk}, profile=self.wp)
		self.assertTrue(form.is_valid())
		self.assertEqual(None, form.save())
		log = self.instance.log.filter(entry_type=ShiftLogEntry.BLOWN)
		self.assertEqual(1, log.count())
		self.assertEqual(log[0].person, self.wp)

	def test_sign_in(self):
		self.assertTrue(self.client.login(username="u", password="pwd"))

		form = SignInForm({"pk": self.once.pk}, profile=self.up)
		self.assertTrue(form.is_valid())
		self.assertEqual(None, form.save())
		log = self.once.log.filter(entry_type=ShiftLogEntry.SIGNIN)
		self.assertEqual(1, log.count())
		self.assertEqual(log[0].person, self.up)

		form = SignInForm({"pk": self.instance.pk}, profile=self.up)
		self.assertFalse(form.is_valid())
		self.assertIn("Workshift is currently filled.", form.errors["pk"])

	def test_sign_out(self):
		self.assertTrue(self.client.login(username="u", password="pwd"))

		form = SignOutForm({"pk": self.instance.pk}, profile=self.up)
		self.assertTrue(form.is_valid())
		self.assertEqual(None, form.save())
		log = self.instance.log.filter(entry_type=ShiftLogEntry.SIGNOUT)
		self.assertEqual(1, log.count())
		self.assertEqual(log[0].person, self.up)

		form = SignOutForm({"pk": self.once.pk}, profile=self.up)
		self.assertFalse(form.is_valid())
		self.assertIn("Cannot sign out of others' workshift.", form.errors["pk"])

class TestPermissions(TestCase):
	"""
	Tests a few basic things about the application: That all the pages can load
	correctly, and that they contain the content that is expected.
	"""
	def setUp(self):
		self.wu = User.objects.create_user(username="wu", password="pwd")
		self.mu = User.objects.create_user(username="mu", password="pwd")
		self.u = User.objects.create_user(username="u", password="pwd")
		self.ou = User.objects.create_user(username="ou", password="pwd")

		self.wm = Manager(
			title="Workshift Manager",
			incumbent=UserProfile.objects.get(user=self.wu),
			workshift_manager=True,
			)
		self.wm.url_title = convert_to_url(self.wm.title)
		self.wm.save()

		self.mm = Manager(
			title="Maintenance Manager",
			incumbent=UserProfile.objects.get(user=self.mu),
			)
		self.mm.url_title = convert_to_url(self.mm.title)
		self.mm.save()

		self.sem = Semester(year=2014, start_date=date.today(),
							end_date=date.today() + timedelta(days=7),
							current=True)
		self.sem.save()

		self.pool = WorkshiftPool(
			semester=self.sem,
			)
		self.pool.save()

		self.hi_pool = WorkshiftPool(
			semester=self.sem,
			title="HI Hours",
			hours=4,
			weeks_per_period=0,
			)
		self.hi_pool.save()

		self.wp = WorkshiftProfile(user=self.wu, semester=self.sem)
		self.mp = WorkshiftProfile(user=self.mu, semester=self.sem)
		self.up = WorkshiftProfile(user=self.u, semester=self.sem)
		self.op = WorkshiftProfile(user=self.ou, semester=self.sem)

		self.wp.save()
		self.mp.save()
		self.up.save()
		self.op.save()

		self.wtype = WorkshiftType(title="Test Posts")
		self.mtype = WorkshiftType(title="Maintenance Cleaning")

		self.wtype.save()
		self.mtype.save()

		self.wshift = RegularWorkshift(
			workshift_type=self.wtype,
			pool=self.pool,
			title="Clean the floors",
			day=DAYS[0][0],
			start_time=datetime.now(),
			end_time=datetime.now() + timedelta(hours=2),
			)
		self.wshift.save()

		self.mshift = RegularWorkshift(
			workshift_type=self.mtype,
			pool=self.hi_pool,
			title="Paint the walls",
			day=DAYS[0][0],
			start_time=datetime.now(),
			end_time=datetime.now() + timedelta(hours=2),
			)
		self.mshift.save()

		self.winstance = WorkshiftInstance(
			weekly_workshift=self.wshift,
			date=date.today(),
			workshifter=self.up,
			)
		self.winstance.save()

		self.minstance = WorkshiftInstance(
			weekly_workshift=self.mshift,
			date=date.today(),
			workshifter=self.up,
			)
		self.minstance.save()

		info = InstanceInfo(
			title="Clean The Deck",
			pool=self.pool,
			description="Make sure to sing sailor tunes.",
			)
		info.save()

		self.wonce = WorkshiftInstance(
			info=info,
			date=date.today(),
			workshifter=self.up,
			)
		self.wonce.save()

		info = InstanceInfo(
			title="Build A Deck",
			pool=self.hi_pool,
			description="Preferably in the shape of a pirate ship.",
			)
		info.save()

		self.monce = WorkshiftInstance(
			info=info,
			date=date.today(),
			workshifter=self.up,
			)
		self.monce.save()

	def test_workshift_manager(self):
		self.assertTrue(self.client.login(username="wu", password="pwd"))

		urls = [
			(True, "/start/"),
			(True, "/"),
			(True, "/profile/{0}/".format(self.up.pk)),
			(True, "/profile/{0}/preferences/".format(self.up.pk)),
			(True, "/manage/"),
			(True, "/manage/assign_shifts/"),
			(True, "/manage/add_workshifter/"),
			(True, "/add_shift/"),
			(True, "/shift/{0}/edit/".format(self.wshift.pk)),
			(True, "/instance/{0}/edit/".format(self.winstance.pk)),
			(True, "/type/{0}/edit/".format(self.wtype.pk)),
			(True, "/shift/{0}/edit/".format(self.mshift.pk)),
			(True, "/instance/{0}/edit/".format(self.minstance.pk)),
			(True, "/type/{0}/edit/".format(self.mtype.pk)),
		]

		for okay, url in urls:
			response = self.client.get("/workshift" + url, follow=True)
			if okay:
				self.assertEqual(response.status_code, 200)
			else:
				self.assertRedirects(response, "/workshift/")
				self.assertIn(MESSAGES["ADMINS_ONLY"], response.content)

	def test_maintenance_manager(self):
		self.assertTrue(self.client.login(username="mu", password="pwd"))

		urls = [
			(False, "/start/"),
			(True, "/"),
			(True, "/profile/{0}/".format(self.up.pk)),
			(False, "/profile/{0}/preferences/".format(self.up.pk)),
			(True, "/manage/"),
			(True, "/manage/assign_shifts/"),
			(False, "/manage/add_workshifter/"),
			(True, "/add_shift/"),
			(False, "/shift/{0}/edit/".format(self.wshift.pk)),
			(False, "/instance/{0}/edit/".format(self.winstance.pk)),
			(False, "/type/{0}/edit/".format(self.wtype.pk)),
			(True, "/shift/{0}/edit/".format(self.mshift.pk)),
			(True, "/instance/{0}/edit/".format(self.minstance.pk)),
			(True, "/type/{0}/edit/".format(self.mtype.pk)),
		]
		for okay, url in urls:
			response = self.client.get("/workshift" + url, follow=True)
			if okay:
				self.assertEqual(response.status_code, 200)
			else:
				self.assertRedirects(response, "/workshift/")
				self.assertIn(MESSAGES["ADMINS_ONLY"], response.content)

	def test_user(self):
		self.assertTrue(self.client.login(username="u", password="pwd"))

		urls = [
			(False, "/start/"),
			(True, "/"),
			(True, "/profile/{0}/".format(self.up.pk)),
			(True, "/profile/{0}/preferences/".format(self.up.pk)),
			(False, "/manage/"),
			(False, "/manage/assign_shifts/"),
			(False, "/manage/add_workshifter/"),
			(False, "/add_shift/"),
			(False, "/shift/{0}/edit/".format(self.wshift.pk)),
			(False, "/instance/{0}/edit/".format(self.winstance.pk)),
			(False, "/type/{0}/edit/".format(self.wtype.pk)),
			(False, "/shift/{0}/edit/".format(self.mshift.pk)),
			(False, "/instance/{0}/edit/".format(self.minstance.pk)),
			(False, "/type/{0}/edit/".format(self.mtype.pk)),
		]

		for okay, url in urls:
			response = self.client.get("/workshift" + url, follow=True)
			if okay:
				self.assertEqual(response.status_code, 200)
			else:
				self.assertRedirects(response, "/workshift/")
				self.assertIn(MESSAGES["ADMINS_ONLY"], response.content)

	def test_other_user(self):
		self.assertTrue(self.client.login(username="ou", password="pwd"))

		urls = [
			(False, "/start/"),
			(True, "/"),
			(True, "/profile/{0}/".format(self.up.pk)),
			(False, "/profile/{0}/preferences/".format(self.up.pk)),
			(False, "/manage/"),
			(False, "/manage/assign_shifts/"),
			(False, "/manage/add_workshifter/"),
			(False, "/add_shift/"),
			(False, "/shift/{0}/edit/".format(self.wshift.pk)),
			(False, "/instance/{0}/edit/".format(self.winstance.pk)),
			(False, "/type/{0}/edit/".format(self.wtype.pk)),
			(False, "/shift/{0}/edit/".format(self.mshift.pk)),
			(False, "/instance/{0}/edit/".format(self.minstance.pk)),
			(False, "/type/{0}/edit/".format(self.mtype.pk)),
		]

		for okay, url in urls:
			response = self.client.get("/workshift" + url, follow=True)
			if okay:
				self.assertEqual(response.status_code, 200)
			else:
				self.assertRedirects(response, "/workshift/")
				self.assertIn(MESSAGES["ADMINS_ONLY"], response.content)

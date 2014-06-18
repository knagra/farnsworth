
from __future__ import absolute_import

from django.conf import settings
from django.test import TestCase

from datetime import date, timedelta, datetime, time

from utils.variables import DAYS, MESSAGES
from utils.funcs import convert_to_url
from base.models import User, UserProfile
from managers.models import Manager
from workshift.models import *
from workshift.forms import *

class TestStart(TestCase):
	def setUp(self):
		self.u = User.objects.create_user(username="u", password="pwd")
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

	def test_unauthenticated(self):
		self.client.logout()
		response = self.client.get("/workshift/", follow=True)
		self.assertRedirects(response, "/login/?next=/workshift/")

	def test_before(self):
		response = self.client.get("/workshift/", follow=True)
		self.assertRedirects(response, "/workshift/start/")

		self.client.logout()
		self.assertTrue(self.client.login(username="u", password="pwd"))

		response = self.client.get("/workshift/", follow=True)
		self.assertRedirects(response, "/")

	def test_starting_month(self):
		# Starting in Summer / Fall / Spring
		pass

	def test_start(self):
		response = self.client.post("/workshift/start/", {
			"season": Semester.SUMMER,
			"year": 2014,
			"rate": 13.30,
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
			2,
			)
		self.assertEqual(
			WorkshiftPool.objects.filter(semester=semester).count(),
			1,
			)

		pool = WorkshiftPool.objects.get(semester=semester)

		self.assertEqual(PoolHours.objects.filter(pool=pool).count(), 2)

		pool_hours = PoolHours.objects.filter(pool=pool)

		for profile in WorkshiftProfile.objects.filter(semester=semester):
			self.assertIn(profile.pool_hours.all()[0], pool_hours)

class TestViews(TestCase):
	"""
	Tests a few basic things about the application: That all the pages can load
	correctly, and that they contain the content that is expected.
	"""
	def setUp(self):
		self.u = User.objects.create_user(username="u", password="pwd")
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
			current_assignee=self.wprofile,
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

		self.open_instance = WorkshiftInstance(
			weekly_workshift=self.shift,
			date=date.today(),
			)
		self.open_instance.save()

		info = InstanceInfo(
			title="Test One Time Shift",
			pool=self.pool,
			description="One Time Description",
			)
		info.save()

		self.once = WorkshiftInstance(
			info=info,
			date=date(2014, 1, 1),
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

		self.instance.logs = [self.sle0, self.sle1, self.sle2, self.sle3, self.sle4]
		self.once.logs = [self.sle0, self.sle1, self.sle2, self.sle3, self.sle4]

		self.instance.save()
		self.once.save()

		self.assertTrue(self.client.login(username="wu", password="pwd"))

	def test_no_profile(self):
		self.client.logout()
		self.client.login(username='u', password='pwd')

		urls = [
			"/types/",
			"/type/{0}/".format(self.wtype.pk),
			"/",
			"/profile/{0}/".format(self.wprofile.user.username),
			"/shift/{0}/".format(self.shift.pk),
			"/instance/{0}/".format(self.instance.pk),
			"/instance/{0}/".format(self.once.pk),
			]
		for url in urls:
			response = self.client.get("/workshift" + url)
			self.assertEqual(response.status_code, 200)

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
			"/profile/{0}/".format(self.wprofile.user.username),
			"/profile/{0}/preferences/".format(self.wprofile.user.username),
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

	def test_type_list(self):
		response = self.client.get("/workshift/types/")
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, self.wtype.title)
		self.assertContains(response, str(self.wtype.hours))
		self.assertNotContains(response, self.wtype.quick_tips)
		self.assertNotContains(response, self.wtype.description)

	def test_type(self):
		response = self.client.get("/workshift/type/{0}/".format(self.wtype.pk))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, self.wtype.title)
		self.assertContains(response, str(self.wtype.hours))
		self.assertContains(response, self.wtype.quick_tips)
		self.assertContains(response, self.wtype.description)

	def test_type_edit(self):
		response = self.client.get("/workshift/type/{0}/edit/".format(self.wtype.pk))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, self.wtype.title)
		self.assertContains(response, str(self.wtype.hours))
		self.assertContains(response, self.wtype.quick_tips)
		self.assertContains(response, self.wtype.description)

	def test_shift(self):
		response = self.client.get("/workshift/shift/{0}/".format(self.shift.pk))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, self.shift.title)
		self.assertContains(response, str(self.shift.hours))
		self.assertContains(response, self.shift.workshift_type.quick_tips)
		self.assertContains(response, self.shift.workshift_type.description)
		self.assertContains(response, self.shift.current_assignee.user.get_full_name())

	def test_edit_shift(self):
		response = self.client.get("/workshift/shift/{0}/edit/".format(self.shift.pk))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, self.shift.title)
		self.assertContains(response, str(self.shift.hours))
		self.assertContains(response, self.shift.current_assignee.user.get_full_name())

	def test_instance(self):
		response = self.client.get("/workshift/instance/{0}/"
								   .format(self.instance.pk))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, self.instance.weekly_workshift.title)
		self.assertContains(response, self.instance.weekly_workshift.pool.title)
		self.assertContains(response, self.instance.workshifter.user.get_full_name())
		self.assertContains(response, str(self.instance.hours))
		self.assertContains(response, self.sle0.note)
		self.assertContains(response, self.sle1.note)
		self.assertContains(response, self.sle2.note)
		self.assertContains(response, self.sle3.note)
		self.assertContains(response, self.sle4.note)

	def test_edit_instance(self):
		response = self.client.get("/workshift/instance/{0}/edit/"
								   .format(self.instance.pk))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, self.instance.weekly_workshift.title)
		self.assertContains(response, self.instance.weekly_workshift.pool.title)
		self.assertContains(response, str(self.instance.date))
		self.assertContains(response, self.instance.workshifter.user.get_full_name())
		self.assertContains(response, str(self.instance.hours))

	def test_one_time(self):
		response = self.client.get("/workshift/instance/{0}/".format(self.once.pk))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, self.once.title)
		self.assertContains(response, self.once.pool.title)
		self.assertContains(response, self.once.description)
		self.assertContains(response, str(self.once.hours))
		self.assertContains(response, self.once.workshifter.user.get_full_name())
		self.assertContains(response, self.sle0.note)
		self.assertContains(response, self.sle1.note)
		self.assertContains(response, self.sle2.note)
		self.assertContains(response, self.sle3.note)
		self.assertContains(response, self.sle4.note)

	def test_edit_one_time(self):
		response = self.client.get("/workshift/instance/{0}/edit/".format(self.once.pk))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, self.once.title)
		self.assertContains(response, self.once.pool.title)
		self.assertContains(response, self.once.description)
		self.assertContains(response, str(self.once.hours))
		self.assertContains(
			response,
			self.once.workshifter.user.get_full_name(),
			)

	def test_semester_view(self):
		response = self.client.get("/workshift/")
		self.assertEqual(response.status_code, 200)

	def test_semester_no_prev(self):
		today = self.sem.start_date
		yesterday = today - timedelta(days=1)
		tomorrow = today + timedelta(days=1)
		response = self.client.get("/workshift/?day=" + today.strftime("%F"))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, today.strftime("%A, %B"))
		self.assertContains(response, today.strftime("%d, %Y"))
		self.assertNotContains(response, "?day=" + yesterday.strftime("%F"))
		self.assertContains(response, "?day=" + tomorrow.strftime("%F"))

	def test_semester_no_next(self):
		today = self.sem.end_date
		yesterday = today - timedelta(days=1)
		tomorrow = today + timedelta(days=1)
		response = self.client.get("/workshift/?day=" + today.strftime("%F"))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, today.strftime("%A, %B"))
		self.assertContains(response, today.strftime("%d, %Y"))
		self.assertContains(response, "?day=" + yesterday.strftime("%F"))
		self.assertNotContains(response, "?day=" + tomorrow.strftime("%F"))

	def test_semester_bad_day(self):
		pass

class TestPreferences(TestCase):
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

		self.w1 = WorkshiftType(
			title="Clean Pots",
			description="Clean and sanitize all cooking materials in the dish room",
			quick_tips="Use 6 tablets of quartz!",
			)
		self.w1.save()

		self.w2 = WorkshiftType(
			title="Clean Dishes",
			description="Clean and santize all eating materials in the dish room",
			quick_tips="Make sure there is liquid for the sanitizer!",
			)
		self.w2.save()

		self.w3 = WorkshiftType(
			title="Trash",
			description="Take out the trash, everyone has to do this one.",
			rateable=False,
			)
		self.w3.save()

		self.assertTrue(self.client.login(username="wu", password="pwd"))
		self.url = "/workshift/profile/{0}/preferences/" \
		  .format(self.wprofile.user.username)


	def test_preferences_get(self):
		response = self.client.get("/workshift/profile/{0}/preferences/"
								   .format(self.wprofile.user.username))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, self.w1.title)
		self.assertContains(response, self.w2.title)
		self.assertNotContains(response, self.w1.description)
		self.assertNotContains(response, self.w2.description)
		self.assertContains(
			response,
			'name="rating-TOTAL_FORMS" type="hidden" value="2"',
			)
		self.assertContains(
			response,
			'name="rating-INITIAL_FORMS" type="hidden" value="2"',
			)
		self.assertContains(
			response,
			'name="rating-MAX_NUM_FORMS" type="hidden" value="2"',
			)
		self.assertContains(
			response,
			'name="time-TOTAL_FORMS" type="hidden" value="1"',
			)
		self.assertContains(
			response,
			'name="time-INITIAL_FORMS" type="hidden" value="0"',
			)
		self.assertContains(
			response,
			'name="time-MAX_NUM_FORMS" type="hidden" value="50"',
			)
		# self.assertEqual(self.wprofile.ratings.count(), 0)

	def test_preferences_post(self):
		response = self.client.post(self.url, {
            "rating-0-id": 1,
            "rating-0-rating": WorkshiftRating.LIKE,
            "rating-1-id": 2,
            "rating-1-rating": WorkshiftRating.DISLIKE,
            "rating-TOTAL_FORMS": 2,
            "rating-INITIAL_FORMS": 2,
            "rating-MAX_NUM_FORMS": 2,
            "time-0-preference": TimeBlock.BUSY,
            "time-0-day": DAYS[0][0], # Monday
            "time-0-start_time": "8:00 AM",
            "time-0-end_time": "5:00 PM",
            "time-1-preference": TimeBlock.FREE,
            "time-1-day": DAYS[-1][0], # Sunday
            "time-1-start_time": "4:00 PM",
            "time-1-end_time": "9:00 PM",
            "time-2-preference": TimeBlock.PREFERRED,
            "time-2-day": DAYS[1][0], # Tuesday
            "time-2-start_time": "6:00 PM",
            "time-2-end_time": "10:00 PM",
            "time-TOTAL_FORMS": 3,
            "time-INITIAL_FORMS": 0,
            "time-MAX_NUM_FORMS": 50,
            "note": "Dishes are fun, pots are cathartic.",
            }, follow=True)

		self.assertRedirects(response, self.url)
		self.assertContains(response, "Preferences saved.")

		self.assertEqual(self.wprofile.ratings.count(), 2)
		for rating, wtype, liked in zip(
				self.wprofile.ratings.all(),
				[self.w1, self.w2],
				[WorkshiftRating.LIKE, WorkshiftRating.DISLIKE],
				):
			self.assertEqual(rating.workshift_type, wtype)
			self.assertEqual(rating.rating, liked)

		self.assertEqual(self.wprofile.time_blocks.count(), 3)
		for block, preference, day, start, end, in zip(
				self.wprofile.time_blocks.all(),
				[TimeBlock.BUSY, TimeBlock.FREE, TimeBlock.PREFERRED],
				[DAYS[0][0], DAYS[-1][0], DAYS[1][0]],
				[time(8, 0, 0), time(16, 0, 0), time(18, 0, 0)],
				[time(17, 0, 0), time(21, 0, 0), time(22, 0, 0)],
				):
			self.assertEqual(block.preference, preference)
			self.assertEqual(block.day, day)
			self.assertEqual(block.start_time, start)
			self.assertEqual(block.end_time, end)

		self.assertEqual(WorkshiftProfile.objects.get(user=self.wu).note,
						 "Dishes are fun, pots are cathartic.")

	def test_no_note(self):
		response = self.client.post(self.url, {
            "rating-0-id": 1,
            "rating-0-rating": WorkshiftRating.LIKE,
            "rating-1-id": 2,
            "rating-1-rating": WorkshiftRating.DISLIKE,
            "rating-TOTAL_FORMS": 2,
            "rating-INITIAL_FORMS": 2,
            "rating-MAX_NUM_FORMS": 2,
            "time-TOTAL_FORMS": 0,
            "time-INITIAL_FORMS": 0,
            "time-MAX_NUM_FORMS": 50,
            }, follow=True)

		self.assertRedirects(response, self.url)
		self.assertContains(response, "Preferences saved.")

	def test_preferences_after_add(self):
		self.test_no_note()
		self.assertEqual(self.wprofile.ratings.count(), 2)

		w4 = WorkshiftType(
			title="Added late",
			description="Workshift added after preferences entered",
			)
		w4.save()

		response = self.client.get(self.url)
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, w4.title)

		response = self.client.post(self.url, {
            "rating-0-id": 1,
            "rating-0-rating": WorkshiftRating.LIKE,
            "rating-1-id": 2,
            "rating-1-rating": WorkshiftRating.DISLIKE,
            "rating-2-id": 3,
            "rating-2-rating": WorkshiftRating.LIKE,
            "rating-TOTAL_FORMS": 3,
            "rating-INITIAL_FORMS": 3,
            "rating-MAX_NUM_FORMS": 3,
            "time-TOTAL_FORMS": 0,
            "time-INITIAL_FORMS": 0,
            "time-MAX_NUM_FORMS": 50,
			}, follow=True)

		self.assertRedirects(response, self.url)
		self.assertContains(response, "Preferences saved.")

		self.assertEqual(self.wprofile.ratings.count(), 3)
		rating = self.wprofile.ratings.get(workshift_type=w4)
		self.assertEqual(rating.rating, WorkshiftRating.LIKE)

	def test_delete_rating(self):
		"""
		Ensure that users cannot delete their rating preferences.
		"""
		self.client.post(self.url, {
            "rating-0-id": 1,
            "rating-0-rating": WorkshiftRating.LIKE,
            "rating-TOTAL_FORMS": 1,
            "rating-INITIAL_FORMS": 2,
            "rating-MAX_NUM_FORMS": 2,
            "time-TOTAL_FORMS": 0,
            "time-INITIAL_FORMS": 0,
            "time-MAX_NUM_FORMS": 50,
            })

		self.assertEqual(self.wprofile.ratings.count(), 2)

	def test_add_rating(self):
		"""
		Ensure that users cannot add extra rating preferences.
		"""
		response = self.client.post(self.url, {
            "rating-0-id": 1,
            "rating-0-rating": WorkshiftRating.LIKE,
            "rating-1-id": 2,
            "rating-1-rating": WorkshiftRating.LIKE,
            "rating-2-id": 3 + 1,
            "rating-2-rating": WorkshiftRating.LIKE,
            "rating-TOTAL_FORMS": 3,
            "rating-INITIAL_FORMS": 2,
            "rating-MAX_NUM_FORMS": 3,
            "time-TOTAL_FORMS": 0,
            "time-INITIAL_FORMS": 0,
            "time-MAX_NUM_FORMS": 50,
            })

		self.assertEqual(response.status_code, 200)
		self.assertEqual(self.wprofile.ratings.count(), 2)

	def test_unrateable(self):
		"""
		Ensure that users cannot rate unrateable shifts.
		"""
		response = self.client.post(self.url, {
            "rating-0-id": 1,
            "rating-0-rating": WorkshiftRating.LIKE,
            "rating-1-id": 3,
            "rating-1-rating": WorkshiftRating.LIKE,
            "rating-TOTAL_FORMS": 2,
            "rating-INITIAL_FORMS": 2,
            "rating-MAX_NUM_FORMS": 2,
            "time-TOTAL_FORMS": 0,
            "time-INITIAL_FORMS": 0,
            "time-MAX_NUM_FORMS": 50,
            })

		self.assertEqual(response.status_code, 200)
		self.assertContains(
			response,
			"That choice is not one of the available choices.",
			)
		self.assertEqual(self.wprofile.ratings.count(), 2)

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

		self.instance.logs = [self.sle0]
		self.once.logs = [self.sle0]

		self.instance.save()
		self.once.save()

	def test_verify(self):
		self.assertTrue(self.client.login(username="u", password="pwd"))

		form = VerifyShiftForm({"pk": self.instance.pk}, profile=self.up)
		self.assertTrue(form.is_valid())
		self.assertEqual(None, form.save())
		log = self.instance.logs.filter(entry_type=ShiftLogEntry.VERIFY)
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
		log = self.instance.logs.filter(entry_type=ShiftLogEntry.VERIFY)
		self.assertEqual(1, log.count())
		self.assertEqual(log[0].person, self.op)

	def test_blown(self):
		self.assertTrue(self.client.login(username="ou", password="pwd"))

		form = BlownShiftForm({"pk": self.instance.pk}, profile=self.op)
		self.assertTrue(form.is_valid())
		self.assertEqual(None, form.save())
		log = self.instance.logs.filter(entry_type=ShiftLogEntry.BLOWN)
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
		log = self.instance.logs.filter(entry_type=ShiftLogEntry.BLOWN)
		self.assertEqual(1, log.count())
		self.assertEqual(log[0].person, self.wp)

	def test_sign_in(self):
		self.assertTrue(self.client.login(username="u", password="pwd"))

		form = SignInForm({"pk": self.once.pk}, profile=self.up)
		self.assertTrue(form.is_valid())
		self.assertEqual(None, form.save())
		log = self.once.logs.filter(entry_type=ShiftLogEntry.SIGNIN)
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
		log = self.instance.logs.filter(entry_type=ShiftLogEntry.SIGNOUT)
		self.assertEqual(1, log.count())
		self.assertEqual(log[0].person, self.up)

		form = SignOutForm({"pk": self.once.pk}, profile=self.up)
		self.assertFalse(form.is_valid())
		self.assertIn("Cannot sign out of others' workshift.", form.errors["pk"])

	def test_missing_shift(self):
		pass

	def test_closed_shift(self):
		pass

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
			"/start/",
			"/",
			"/profile/{0}/".format(self.up.user.username),
			"/profile/{0}/preferences/".format(self.up.user.username),
			"/manage/",
			"/manage/assign_shifts/",
			"/manage/add_workshifter/",
			"/add_shift/",
			"/shift/{0}/edit/".format(self.wshift.pk),
			"/instance/{0}/edit/".format(self.winstance.pk),
			"/type/{0}/edit/".format(self.wtype.pk),
			"/shift/{0}/edit/".format(self.mshift.pk),
			"/instance/{0}/edit/".format(self.minstance.pk),
			"/type/{0}/edit/".format(self.mtype.pk),
		]

		for url in urls:
			response = self.client.get("/workshift" + url, follow=True)
			self.assertEqual(response.status_code, 200)

	def test_maintenance_manager(self):
		self.assertTrue(self.client.login(username="mu", password="pwd"))

		urls = [
			(False, "/start/"),
			(True, "/"),
			(True, "/profile/{0}/".format(self.up.user.username)),
			(False, "/profile/{0}/preferences/".format(self.up.user.username)),
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
				self.assertContains(response, MESSAGES["ADMINS_ONLY"])

	def test_user(self):
		self.assertTrue(self.client.login(username="u", password="pwd"))

		urls = [
			(False, "/start/"),
			(True, "/"),
			(True, "/profile/{0}/".format(self.up.user.username)),
			(True, "/profile/{0}/preferences/".format(self.up.user.username)),
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
				self.assertContains(response, MESSAGES["ADMINS_ONLY"])

	def test_other_user(self):
		self.assertTrue(self.client.login(username="ou", password="pwd"))

		urls = [
			(False, "/start/"),
			(True, "/"),
			(True, "/profile/{0}/".format(self.up.user.username)),
			(False, "/profile/{0}/preferences/".format(self.up.user.username)),
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
				self.assertContains(response, MESSAGES["ADMINS_ONLY"])

class TestWorkshifters(TestCase):
	def setUp(self):
		pass

	def test_no_alumni(self):
		pass

	def test_add_workshifter(self):
		pass

class TestWorkshifts(TestCase):
	def setUp(self):
		self.wu = User.objects.create_user(username="wu", password="pwd")

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

		self.wp = WorkshiftProfile(user=self.wu, semester=self.sem)
		self.wp.save()

		self.type = WorkshiftType(title="Test Posts")
		self.type.save()

		self.shift = RegularWorkshift(
			workshift_type=self.type,
			pool=self.pool,
			title="Clean the floors",
			day=DAYS[0][0],
			start_time=datetime.now(),
			end_time=datetime.now() + timedelta(hours=2),
			)
		self.shift.save()

		self.instance = WorkshiftInstance(
			weekly_workshift=self.shift,
			date=date.today(),
			workshifter=self.wp,
			)
		self.instance.save()

		info = InstanceInfo(
			title="Clean The Deck",
			pool=self.pool,
			description="Make sure to sing sailor tunes.",
			)
		info.save()

		self.once = WorkshiftInstance(
			info=info,
			date=date.today(),
			workshifter=self.wp,
			)
		self.once.save()

		self.client.login(username="wu", password="pwd")

	def test_add_instance(self):
		url = "/workshift/add_shift/"
		response = self.client.post(url, {
			"instance": "",
			}, follow=True)
		self.assertRedirects(response, "/workshift/manage/")

	def test_edit_instance(self):
		url = "/workshift/instance/{0}/edit/".format(self.instance.pk)
		response = self.client.post(url, {
			"edit": "",
			}, follow=True)
		self.assertRedirects(response, "/workshift/instance/{0}/".format(self.instance.pk))

	def test_delete_instance(self):
		url = "/workshift/instance/{0}/edit/".format(self.instance.pk)
		response = self.client.post(url, {
			"delete": "",
			}, follow=True)
		self.assertRedirects(response, "/workshift/manage/")

	def test_add_once(self):
		url = "/workshift/add_shift/"
		response = self.client.post(url, {
			"instance": "",
			}, follow=True)
		self.assertRedirects(response, "/workshift/manage/")

	def test_edit_once(self):
		url = "/workshift/instance/{0}/edit/".format(self.once.pk)
		response = self.client.post(url, {
			"edit": "",
			}, follow=True)
		self.assertRedirects(response, "/workshift/instance/{0}/".format(self.once.pk))

	def test_delete_once(self):
		url = "/workshift/instance/{0}/edit/".format(self.once.pk)
		response = self.client.post(url, {
			"delete": "",
			}, follow=True)
		self.assertRedirects(response, "/workshift/manage/")

	def test_add_shift(self):
		url = "/workshift/add_shift/"
		response = self.client.post(url, {
			"shift": "",
			}, follow=True)
		self.assertRedirects(response, "/workshift/manage/")

	def test_edit_shift(self):
		url = "/workshift/shift/{0}/edit/".format(self.shift.pk)
		response = self.client.post(url, {
			"edit": "",
			}, follow=True)
		self.assertRedirects(response, "/workshift/shift/{0}/".format(self.shift.pk))

	def test_delete_shift(self):
		url = "/workshift/shift/{0}/edit/".format(self.shift.pk)
		response = self.client.post(url, {
			"delete": "",
			}, follow=True)
		self.assertRedirects(response, "/workshift/manage/")

	def test_add_type(self):
		url = "/workshift/add_shift/"
		response = self.client.post(url, {
			"type": "",
			}, follow=True)
		self.assertRedirects(response, "/workshift/manage/")

	def test_edit_type(self):
		url = "/workshift/type/{0}/edit/".format(self.type.pk)
		response = self.client.post(url, {
			"edit": "",
			}, follow=True)
		self.assertRedirects(response, "/workshift/type/{0}/".format(self.type.pk))

	def test_delete_type(self):
		url = "/workshift/type/{0}/edit/".format(self.type.pk)
		response = self.client.post(url, {
			"delete": "",
			}, follow=True)
		self.assertRedirects(response, "/workshift/manage/")

class TestSemester(TestCase):
	def setUp(self):
		self.wu = User.objects.create_user(username="wu", password="pwd")

		self.wm = Manager(
			title="Workshift Manager",
			incumbent=UserProfile.objects.get(user=self.wu),
			workshift_manager=True,
			)
		self.wm.url_title = convert_to_url(self.wm.title)
		self.wm.save()

		self.s1 = Semester(year=2014, start_date=date.today(),
						   end_date=date.today() + timedelta(days=7),
						   current=True)
		self.s1.save()

		self.s2 = Semester(year=2013, start_date=date.today(),
						   end_date=date.today() + timedelta(days=7),
						   current=False)
		self.s2.save()

		self.wprofile = WorkshiftProfile(user=self.wu, semester=self.s1)
		self.wprofile.save()

		self.client.login(username="wu", password="pwd")

	def test_no_current(self):
		self.s1.current = False
		self.s1.save()

		response = self.client.get("/workshift/", follow=True)
		self.assertRedirects(response, "/workshift/start/")

	def test_multiple_current(self):
		self.s2.current = True
		self.s2.save()

		response = self.client.get("/workshift/")
		self.assertContains(
			response,
			MESSAGES['MULTIPLE_CURRENT_SEMESTERS'].format(
				admin_email=settings.ADMINS[0][1],
				workshift_emails="",
				))

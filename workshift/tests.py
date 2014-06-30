
from __future__ import absolute_import

from django.conf import settings
from django.test import TestCase
from django.utils.timezone import utc

from datetime import date, timedelta, datetime, time
from weekday_field.utils import DAY_CHOICES

from utils.variables import MESSAGES
from base.models import User, UserProfile
from managers.models import Manager
from workshift.models import *
from workshift.forms import *
from workshift import utils

class TestStart(TestCase):
	def setUp(self):
		self.u = User.objects.create_user(username="u", password="pwd")
		self.wu = User.objects.create_user(username="wu", password="pwd")

		self.wu.first_name, self.wu.last_name = "Cooperative", "User"
		self.wu.save()

		self.wm = Manager.objects.create(
			title="Workshift Manager",
			incumbent=UserProfile.objects.get(user=self.wu),
			workshift_manager=True,
			)

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
			1,
			Semester.objects.filter(year=2014).filter(season=Semester.SUMMER).count(),
			)

		semester = Semester.objects.get(year=2014, season=Semester.SUMMER)

		self.assertEqual(
			2,
			WorkshiftProfile.objects.filter(semester=semester).count(),
			)
		self.assertEqual(
			1,
			WorkshiftPool.objects.filter(semester=semester).count(),
			)

		pool = WorkshiftPool.objects.get(semester=semester)

		self.assertEqual(PoolHours.objects.filter(pool=pool).count(), 2)

		pool_hours = PoolHours.objects.filter(pool=pool)

		for profile in WorkshiftProfile.objects.filter(semester=semester):
			self.assertEqual(1, profile.pool_hours.count())
			self.assertIn(profile.pool_hours.all()[0], pool_hours)
			self.assertEqual(1, profile.pool_hours.filter(pool=pool).count())

class TestUtils(TestCase):
	def setUp(self):
		self.u = User.objects.create_user(username="u", password="pwd")
		self.semester = Semester.objects.create(
			year=2014,
			season=Semester.SUMMER,
			start_date=date(2014, 5, 25),
			end_date=date(2014, 8, 16),
			)
		self.profile = WorkshiftProfile.objects.create(
			user=self.u,
			semester=self.semester,
			)
		self.p1 = WorkshiftPool.objects.create(
			title="Regular Workshift",
			is_primary=True,
			semester=self.semester,
			sign_out_cutoff=24,
			)
		self.p2 = WorkshiftPool.objects.create(
			title="Alternate Workshift",
			semester=self.semester,
			)

	def test_get_year_season(self):
		year, season = utils.get_year_season()
		self.assertLess(abs(year - date.today().year), 2)
 		self.assertIn(season, [Semester.SPRING, Semester.SUMMER, Semester.FALL])

	def test_starting_month(self):
		# Starting in Summer / Fall / Spring
		self.assertEqual(
			(2015, Semester.SPRING),
			utils.get_year_season(day=date(2014, 12, 20)),
			)
		self.assertEqual(
			(2015, Semester.SPRING),
			utils.get_year_season(day=date(2015, 3, 20)),
			)
		self.assertEqual(
			(2014, Semester.SUMMER),
			utils.get_year_season(day=date(2014, 4, 1)),
			)
		self.assertEqual(
			(2014, Semester.SUMMER),
			utils.get_year_season(day=date(2014, 7, 20)),
			)
		self.assertEqual(
			(2014, Semester.FALL),
			utils.get_year_season(day=date(2014, 8, 1)),
			)
		self.assertEqual(
			(2014, Semester.FALL),
			utils.get_year_season(day=date(2014, 10, 20)),
			)

	def test_start_end(self):
		self.assertEqual(
			(date(2014, 1, 20), date(2014, 5, 17)),
			utils.get_semester_start_end(2014, Semester.SPRING),
			)
		self.assertEqual(
			(date(2014, 5, 25), date(2014, 8, 16)),
			utils.get_semester_start_end(2014, Semester.SUMMER),
			)
		self.assertEqual(
			(date(2014, 8, 24), date(2014, 12, 20)),
			utils.get_semester_start_end(2014, Semester.FALL),
			)

	def test_make_pool_hours_all(self):
		utils.make_workshift_pool_hours()
		self.assertEqual(2, PoolHours.objects.count())
		self.assertEqual(2, self.profile.pool_hours.count())

	def test_make_pool_hours_profile(self):
		utils.make_workshift_pool_hours(
			semester=self.semester,
			profiles=[],
			)
		self.assertEqual(0, PoolHours.objects.count())
		self.assertEqual(0, self.profile.pool_hours.count())

		utils.make_workshift_pool_hours(
			semester=self.semester,
			profiles=[self.profile],
			)
		self.assertEqual(2, PoolHours.objects.count())
		self.assertEqual(2, self.profile.pool_hours.count())

	def test_make_pool_hours_pools(self):
		utils.make_workshift_pool_hours(
			semester=self.semester,
			pools=[self.p1],
			)
		self.assertEqual(1, PoolHours.objects.count())
		self.assertEqual(1, self.profile.pool_hours.count())

		utils.make_workshift_pool_hours(
			semester=self.semester,
			pools=[self.p2],
			)
		self.assertEqual(2, PoolHours.objects.count())
		self.assertEqual(2, self.profile.pool_hours.count())

	def test_make_pool_hours_primary(self):
		utils.make_workshift_pool_hours(
			semester=self.semester,
			primary_hours=6,
			)
		self.assertEqual(6, PoolHours.objects.get(pool=self.p1).hours)
		self.assertEqual(self.p2.hours, PoolHours.objects.get(pool=self.p2).hours)

	def test_int_days(self):
		self.assertEqual([0], utils.get_int_days("Monday"))
		self.assertEqual([1], utils.get_int_days(["Tuesday"]))
		self.assertEqual([0, 1, 2, 3, 4, 5, 6], utils.get_int_days(["Any day"]))
		self.assertEqual([0, 1, 2, 3, 4], utils.get_int_days(["Weekdays"]))
		self.assertEqual([5, 6], utils.get_int_days(["Weekends"]))

	def test_can_manage(self):
		pass

	def test_is_available(self):
		pass

	def test_make_instances(self):
		wtype = WorkshiftType.objects.create(
			title="Test Make Instances",
			)
		shift = RegularWorkshift.objects.create(
			title="Test Shift",
			workshift_type=wtype,
			pool=self.p1,
			days=[0, 1, 2, 3, 4],
			current_assignee=self.profile,
			hours=7,
			)
		WorkshiftInstance.objects.create(
			weekly_workshift=shift,
			date=date.today() - timedelta(date.today().weekday())
			)
		instances = make_instances(
			semester=self.semester,
			shifts=[shift],
			)

		for instance in instances:
			self.assertEqual("Test Shift", instance.title)
			self.assertEqual(shift, instance.weekly_workshift)
			self.assertEqual(7, instance.hours)
			self.assertEqual(7, instance.intended_hours)

		self.assertEqual(set(shift.days), set(i.date.weekday() for i in instances))

	def test_collect_blown(self):
		utils.make_workshift_pool_hours()
		self.assertEqual(
			([], []),
			utils.collect_blown(),
			)

		self.assertEqual(
			([], []),
			utils.collect_blown(semester=self.semester),
			)

		now = datetime(2014, 6, 1, 20, 0, 0).replace(tzinfo=utc)
		past = datetime(2014, 5, 31, 20, 0, 0).replace(tzinfo=utc)
		WorkshiftInstance.objects.create(
			info=InstanceInfo.objects.create(
				title="Closed",
				pool=self.p1,
				),
			closed=True,
			date=past.date(),
			semester=self.semester,
			)
		to_close = WorkshiftInstance.objects.create(
			info=InstanceInfo.objects.create(
				title="To be closed",
				pool=self.p1,
				),
			date=past.date(),
			semester=self.semester,
			)
		WorkshiftInstance.objects.create(
			info=InstanceInfo.objects.create(
				title="Not Blown",
				pool=self.p1,
				),
			date=now.date(),
			semester=self.semester,
			)
		blown = WorkshiftInstance.objects.create(
			info=InstanceInfo.objects.create(
				title="Blown",
				pool=self.p1,
				),
			date=past.date(),
			workshifter=self.profile,
			semester=self.semester,
			)
		WorkshiftInstance.objects.create(
			info=InstanceInfo.objects.create(
				title="Edge Case 1: Not Closed",
				end_time=now.time(),
				pool=self.p1,
				),
			date=now.date(),
			semester=self.semester,
			)
		edge_case_2 = WorkshiftInstance.objects.create(
			info=InstanceInfo.objects.create(
				title="Edge Case 2: Closed",
				end_time=time(19, 59),
				pool=self.p1,
				),
			date=now.date(),
			)
		signed_out_1 = WorkshiftInstance.objects.create(
			info=InstanceInfo.objects.create(
				title="Workshifter signed out early enough",
				pool=self.p1,
				),
			date=past.date(),
			semester=self.semester,
			)
		log = ShiftLogEntry.objects.create(
			entry_type=ShiftLogEntry.SIGNOUT,
			person=self.profile,
			)
		log.entry_time = datetime(2014, 5, 26, 0).replace(tzinfo=utc)
		log.save()
		signed_out_1.logs.add(log)
		signed_out_1.save()
		signed_out_2 = WorkshiftInstance.objects.create(
			info=InstanceInfo.objects.create(
				title="Workshifter signed out too late",
				pool=self.p1,
				),
			date=past.date(),
			semester=self.semester,
			)
		log = ShiftLogEntry.objects.create(
			entry_type=ShiftLogEntry.SIGNOUT,
			person=self.profile,
			)
		log.entry_time = datetime(2014, 5, 31, 0).replace(tzinfo=utc)
		log.save()
		signed_out_2.logs.add(log)
		signed_out_2.save()
		self.assertEqual(
			([to_close, edge_case_2, signed_out_1], [blown, signed_out_2]),
			utils.collect_blown(now=now),
			)

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

		self.wm = Manager.objects.create(
			title="Workshift Manager",
			incumbent=UserProfile.objects.get(user=self.wu),
			workshift_manager=True,
			)

		self.sem = Semester.objects.create(
			year=2014, start_date=date.today(),
			end_date=date.today() + timedelta(days=7),
			current=True,
			)

		self.pool = WorkshiftPool.objects.create(
			semester=self.sem,
			)
		self.pool.managers = [self.wm]
		self.pool.save()

		self.wprofile = WorkshiftProfile.objects.create(
			user=self.wu,
			semester=self.sem,
			)

		self.wtype = WorkshiftType.objects.create(
			title="Test Posts",
			description="Test WorkshiftType Description",
			quick_tips="Test Quick Tips",
			)

		self.shift = RegularWorkshift.objects.create(
			workshift_type=self.wtype,
			current_assignee=self.wprofile,
			pool=self.pool,
			title="Test Regular Shift",
			start_time=datetime.now(),
			end_time=datetime.now() + timedelta(hours=2),
			)
		self.shift.days = [DAY_CHOICES[0][0]]
		self.shift.save()

		self.instance = WorkshiftInstance.objects.create(
			weekly_workshift=self.shift,
			date=date.today(),
			workshifter=self.wprofile,
			)

		self.open_instance = WorkshiftInstance.objects.create(
			weekly_workshift=self.shift,
			date=date.today(),
			)

		info = InstanceInfo.objects.create(
			title="Test One Time Shift",
			pool=self.pool,
			description="One Time Description",
			)

		self.once = WorkshiftInstance.objects.create(
			info=info,
			date=date(2014, 1, 1),
			workshifter=self.wprofile,
			)

		self.sle0 = ShiftLogEntry.objects.create(
			person=self.wprofile,
			note="Test Shift Log #0",
			entry_type=ShiftLogEntry.ASSIGNED,
			)

		self.sle1 = ShiftLogEntry.objects.create(
			person=self.wprofile,
			note="Test Shift Log #1",
			entry_type=ShiftLogEntry.SIGNOUT,
			)

		self.sle2 = ShiftLogEntry.objects.create(
			person=self.wprofile,
			note="Test Shift Log #2",
			entry_type=ShiftLogEntry.SIGNIN,
			)

		self.sle3 = ShiftLogEntry.objects.create(
			person=self.wprofile,
			note="Test Shift Log #3",
			entry_type=ShiftLogEntry.VERIFY,
			)

		self.sle4 = ShiftLogEntry.objects.create(
			person=self.wprofile,
			note="Test Shift Log #4",
			entry_type=ShiftLogEntry.BLOWN,
			)

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
			"/manage/add_shift/",
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
		self.assertContains(response, self.once.hours)
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

		self.wm = Manager.objects.create(
			title="Workshift Manager",
			incumbent=UserProfile.objects.get(user=self.wu),
			workshift_manager=True,
			)

		self.sem = Semester.objects.create(
			year=2014, start_date=date.today(),
			end_date=date.today() + timedelta(days=7),
			current=True,
			)

		self.pool = WorkshiftPool.objects.create(
			semester=self.sem,
			)
		self.pool.managers = [self.wm]
		self.pool.save()

		self.wprofile = WorkshiftProfile.objects.create(
			user=self.wu,
			semester=self.sem,
			)

		self.w1 = WorkshiftType.objects.create(
			title="Clean Pots",
			description="Clean and sanitize all cooking materials in the dish room",
			quick_tips="Use 6 tablets of quartz!",
			)

		self.w2 = WorkshiftType.objects.create(
			title="Clean Dishes",
			description="Clean and santize all eating materials in the dish room",
			quick_tips="Make sure there is liquid for the sanitizer!",
			)

		self.w3 = WorkshiftType.objects.create(
			title="Trash",
			description="Take out the trash, everyone has to do this one.",
			rateable=False,
			)

		self.assertTrue(self.client.login(username="wu", password="pwd"))
		self.url = "/workshift/profile/{0}/preferences/" \
		  .format(self.wprofile.user.username)

	def test_preferences_get(self):
		response = self.client.get("/workshift/profile/{0}/preferences/"
								   .format(self.wprofile.user.username))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, self.w1.title)
		self.assertContains(response, self.w2.title)
		self.assertContains(response, self.w1.description)
		self.assertContains(response, self.w2.description)
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
		self.assertEqual(self.wprofile.ratings.count(), 0)

	def test_preferences_post(self):
		response = self.client.post(self.url, {
			"rating-1-rating": WorkshiftRating.LIKE,
			"rating-2-rating": WorkshiftRating.DISLIKE,
			"time-0-preference": TimeBlock.BUSY,
			"time-0-day": DAY_CHOICES[0][0], # Monday
			"time-0-start_time": "8:00 AM",
			"time-0-end_time": "5:00 PM",
			"time-1-preference": TimeBlock.FREE,
			"time-1-day": DAY_CHOICES[-1][0], # Sunday
			"time-1-start_time": "4:00 PM",
			"time-1-end_time": "9:00 PM",
			"time-2-preference": TimeBlock.PREFERRED,
			"time-2-day": DAY_CHOICES[1][0], # Tuesday
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
				[DAY_CHOICES[0][0], DAY_CHOICES[-1][0], DAY_CHOICES[1][0]],
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
			"rating-1-rating": WorkshiftRating.LIKE,
			"rating-2-rating": WorkshiftRating.DISLIKE,
			"time-TOTAL_FORMS": 0,
			"time-INITIAL_FORMS": 0,
			"time-MAX_NUM_FORMS": 50,
			}, follow=True)

		self.assertRedirects(response, self.url)
		self.assertContains(response, "Preferences saved.")

	def test_preferences_after_add(self):
		self.test_no_note()
		self.assertEqual(self.wprofile.ratings.count(), 2)

		w4 = WorkshiftType.objects.create(
			title="Added late",
			description="Workshift added after preferences entered",
			)

		response = self.client.get(self.url)
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, w4.title)

		response = self.client.post(self.url, {
			"rating-1-rating": WorkshiftRating.LIKE,
			"rating-2-rating": WorkshiftRating.DISLIKE,
			"rating-{0}-rating".format(w4.pk): WorkshiftRating.LIKE,
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
		response = self.client.post(self.url, {
			"rating-1-rating": WorkshiftRating.LIKE,
			"rating-2-rating": WorkshiftRating.LIKE,
			"time-TOTAL_FORMS": 0,
			"time-INITIAL_FORMS": 0,
			"time-MAX_NUM_FORMS": 50,
			}, follow=True)

		self.assertRedirects(response, self.url)

		response = self.client.post(self.url, {
			"rating-1-rating": WorkshiftRating.LIKE,
			"time-TOTAL_FORMS": 0,
			"time-INITIAL_FORMS": 0,
			"time-MAX_NUM_FORMS": 50,
			})

		self.assertEqual(response.status_code, 200)
		self.assertEqual(self.wprofile.ratings.count(), 2)

	def test_add_rating(self):
		"""
		Ensure that users cannot add extra rating preferences.
		"""
		response = self.client.post(self.url, {
			"rating-1-rating": WorkshiftRating.LIKE,
			"rating-2-rating": WorkshiftRating.LIKE,
			"rating-4-rating": WorkshiftRating.LIKE,
			"time-TOTAL_FORMS": 0,
			"time-INITIAL_FORMS": 0,
			"time-MAX_NUM_FORMS": 50,
			})

		self.assertEqual(self.wprofile.ratings.count(), 2)

	def test_unrateable(self):
		"""
		Ensure that users cannot rate unrateable shifts.
		"""
		response = self.client.post(self.url, {
			"rating-1-rating": WorkshiftRating.LIKE,
			"rating-2-rating": WorkshiftRating.LIKE,
			"rating-3-rating": WorkshiftRating.LIKE,
			"time-TOTAL_FORMS": 0,
			"time-INITIAL_FORMS": 0,
			"time-MAX_NUM_FORMS": 50,
			})

		self.assertEqual(self.wprofile.ratings.count(), 2)

class TestInteractForms(TestCase):
	def setUp(self):
		self.wu = User.objects.create_user(username="wu", password="pwd")
		self.u = User.objects.create_user(username="u", password="pwd")
		self.ou = User.objects.create_user(username="ou", password="pwd")

		self.wm = Manager.objects.create(
			title="Workshift Manager",
			incumbent=UserProfile.objects.get(user=self.wu),
			workshift_manager=True,
			)

		self.sem = Semester.objects.create(
			year=2014, start_date=date.today(),
			end_date=date.today() + timedelta(days=7),
			current=True,
			)

		self.pool = WorkshiftPool.objects.create(
			semester=self.sem,
			any_blown=True,
			self_verify=True,
			)
		self.pool.managers = [self.wm]

		self.wp = WorkshiftProfile.objects.create(
			user=self.wu,
			semester=self.sem,
			)
		self.up = WorkshiftProfile.objects.create(
			user=self.u,
			semester=self.sem,
			)
		self.op = WorkshiftProfile.objects.create(
			user=self.ou,
			semester=self.sem,
			)

		ph = PoolHours.objects.create(pool=self.pool)

		self.up.pool_hours = [ph]
		self.up.save()

		self.wtype = WorkshiftType.objects.create(
			title="Test Posts",
			description="Test WorkshiftType Description",
			quick_tips="Test Quick Tips",
			)

		self.shift = RegularWorkshift.objects.create(
			workshift_type=self.wtype,
			pool=self.pool,
			title="Test Regular Shift",
			start_time=datetime.now(),
			end_time=datetime.now() + timedelta(hours=2),
			)
		self.shift.days = [DAY_CHOICES[0][0]]
		self.shift.save()

		self.instance = WorkshiftInstance.objects.create(
			weekly_workshift=self.shift,
			date=date.today(),
			workshifter=self.up,
			)

		info = InstanceInfo.objects.create(
			title="Test One Time Shift",
			pool=self.pool,
			)

		self.once = WorkshiftInstance.objects.create(
			info=info,
			date=date.today(),
			)

		self.sle0 = ShiftLogEntry.objects.create(
			person=self.wp,
			entry_type=ShiftLogEntry.ASSIGNED,
			)

		self.instance.logs = [self.sle0]
		self.once.logs = [self.sle0]

		self.instance.save()
		self.once.save()

	def test_verify(self):
		self.assertTrue(self.client.login(username="u", password="pwd"))

		form = VerifyShiftForm({"pk": self.instance.pk}, profile=self.up)
		self.assertTrue(form.is_valid())
		self.assertIsInstance(form.save(), WorkshiftInstance)
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
		self.assertIsInstance(form.save(), WorkshiftInstance)
		log = self.instance.logs.filter(entry_type=ShiftLogEntry.VERIFY)
		self.assertEqual(1, log.count())
		self.assertEqual(log[0].person, self.op)

	def test_blown(self):
		self.assertTrue(self.client.login(username="ou", password="pwd"))

		form = BlownShiftForm({"pk": self.instance.pk}, profile=self.op)
		self.assertTrue(form.is_valid())
		self.assertIsInstance(form.save(), WorkshiftInstance)
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
		self.assertIsInstance(form.save(), WorkshiftInstance)
		log = self.instance.logs.filter(entry_type=ShiftLogEntry.BLOWN)
		self.assertEqual(1, log.count())
		self.assertEqual(log[0].person, self.wp)

	def test_sign_in(self):
		self.assertTrue(self.client.login(username="u", password="pwd"))

		form = SignInForm({"pk": self.once.pk}, profile=self.up)
		self.assertTrue(form.is_valid())
		self.assertIsInstance(form.save(), WorkshiftInstance)
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
		self.assertIsInstance(form.save(), WorkshiftInstance)
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

		self.wm = Manager.objects.create(
			title="Workshift Manager",
			incumbent=UserProfile.objects.get(user=self.wu),
			workshift_manager=True,
			)

		self.mm = Manager.objects.create(
			title="Maintenance Manager",
			incumbent=UserProfile.objects.get(user=self.mu),
			)

		self.sem = Semester.objects.create(
			year=2014, start_date=date.today(),
			end_date=date.today() + timedelta(days=7),
			current=True,
			)

		self.pool = WorkshiftPool.objects.create(
			semester=self.sem,
			)

		self.hi_pool = WorkshiftPool.objects.create(
			semester=self.sem,
			title="HI Hours",
			hours=4,
			weeks_per_period=0,
			)

		self.wp = WorkshiftProfile.objects.create(user=self.wu, semester=self.sem)
		self.mp = WorkshiftProfile.objects.create(user=self.mu, semester=self.sem)
		self.up = WorkshiftProfile.objects.create(user=self.u, semester=self.sem)
		self.op = WorkshiftProfile.objects.create(user=self.ou, semester=self.sem)

		self.wtype = WorkshiftType.objects.create(title="Test Posts")
		self.mtype = WorkshiftType.objects.create(title="Maintenance Cleaning")

		self.wshift = RegularWorkshift.objects.create(
			workshift_type=self.wtype,
			pool=self.pool,
			title="Clean the floors",
			start_time=datetime.now(),
			end_time=datetime.now() + timedelta(hours=2),
			)
		self.wshift.days = [DAY_CHOICES[0][0]]
		self.wshift.save()

		self.mshift = RegularWorkshift.objects.create(
			workshift_type=self.mtype,
			pool=self.hi_pool,
			title="Paint the walls",
			start_time=datetime.now(),
			end_time=datetime.now() + timedelta(hours=2),
			)
		self.mshift.days = [DAY_CHOICES[0][0]]
		self.mshift.save()

		self.winstance = WorkshiftInstance.objects.create(
			weekly_workshift=self.wshift,
			date=date.today(),
			workshifter=self.up,
			)

		self.minstance = WorkshiftInstance.objects.create(
			weekly_workshift=self.mshift,
			date=date.today(),
			workshifter=self.up,
			)

		info = InstanceInfo.objects.create(
			title="Clean The Deck",
			pool=self.pool,
			description="Make sure to sing sailor tunes.",
			)

		self.wonce = WorkshiftInstance.objects.create(
			info=info,
			date=date.today(),
			workshifter=self.up,
			)

		info = InstanceInfo.objects.create(
			title="Build A Deck",
			pool=self.hi_pool,
			description="Preferably in the shape of a pirate ship.",
			)

		self.monce = WorkshiftInstance.objects.create(
			info=info,
			date=date.today(),
			workshifter=self.up,
			)

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
			"/manage/add_shift/",
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
			(True, "/manage/add_shift/"),
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
			(False, "/manage/add_shift/"),
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
			(False, "/manage/add_shift/"),
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
		self.u = User.objects.create_user(username="u", password="pwd")

		self.wm = Manager.objects.create(
			title="Workshift Manager",
			incumbent=UserProfile.objects.get(user=self.wu),
			workshift_manager=True,
			)

		self.sem = Semester.objects.create(
			year=2014, start_date=date.today(),
			end_date=date.today() + timedelta(days=7),
			current=True,
			)

		self.pool = WorkshiftPool.objects.create(
			semester=self.sem,
			)
		self.pool.managers = [self.wm]
		self.pool.save()

		self.wp = WorkshiftProfile.objects.create(user=self.wu, semester=self.sem)
		self.up = WorkshiftProfile.objects.create(user=self.u, semester=self.sem)

		self.type = WorkshiftType.objects.create(
			title="Test Posts",
			description="Test Description",
			)

		self.shift = RegularWorkshift.objects.create(
			workshift_type=self.type,
			pool=self.pool,
			title="Clean the floors",
			start_time=time(16, 0, 0),
			end_time=time(18, 0, 0)
			)
		self.shift.days = [DAY_CHOICES[0][0]]
		self.shift.save()

		self.instance = WorkshiftInstance.objects.create(
			weekly_workshift=self.shift,
			date=date.today(),
			workshifter=self.wp,
			)

		info = InstanceInfo.objects.create(
			title="Clean The Deck",
			pool=self.pool,
			description="Make sure to sing sailor tunes.",
			)

		self.once = WorkshiftInstance.objects.create(
			info=info,
			date=date.today(),
			workshifter=self.wp,
			)

		self.client.login(username="wu", password="pwd")

	def test_add_instance(self):
		url = "/workshift/manage/add_shift/"
		response = self.client.post(url, {
			"add_instance": "",
			"weekly_workshift": self.shift.pk,
			"date": "05/27/2014",
			"workshifter": self.wp.pk,
			"closed": False,
			"hours": 2,
			"auto_verify": False,
			"week_long": False,
			}, follow=True)
		self.assertRedirects(response, "/workshift/manage/")
		instance = WorkshiftInstance.objects.get(pk=self.once.pk + 1)
		self.assertEqual(instance.weekly_workshift, self.shift)
		self.assertEqual(instance.info, None)
		self.assertEqual(instance.date, date(2014, 5, 27))
		self.assertEqual(instance.workshifter, self.wp)
		self.assertEqual(instance.closed, False)
		self.assertEqual(instance.hours, 2)
		self.assertEqual(instance.auto_verify, False)
		self.assertEqual(instance.week_long, False)

	def test_edit_instance(self):
		url = "/workshift/instance/{0}/edit/".format(self.instance.pk)
		response = self.client.post(url, {
			"edit": "",
			"title": self.instance.title,
			"description": self.instance.description,
			"pool": self.instance.pool.pk,
			"start_time": self.instance.start_time.strftime("%I:%M %p"),
			"end_time": self.instance.end_time.strftime("%I:%M %p"),
			"date": "05/27/2014",
			"workshifter": self.wp.pk,
			"closed": False,
			"hours": 2,
			"auto_verify": False,
			"week_long": False,
			}, follow=True)
		self.assertRedirects(response, "/workshift/instance/{0}/".format(self.instance.pk))
		self.assertEqual(InstanceInfo.objects.count(), 1)
		instance = WorkshiftInstance.objects.get(pk=self.instance.pk)
		self.assertEqual(instance.weekly_workshift, self.instance.weekly_workshift)
		self.assertEqual(instance.title, self.instance.title)
		self.assertEqual(instance.description, self.instance.description)
		self.assertEqual(instance.pool, self.pool)
		self.assertEqual(instance.start_time, self.instance.start_time)
		self.assertEqual(instance.end_time, self.instance.end_time)
		self.assertEqual(instance.date, date(2014, 5, 27))
		self.assertEqual(instance.workshifter, self.wp)
		self.assertEqual(instance.closed, False)
		self.assertEqual(instance.hours, 2)
		self.assertEqual(instance.auto_verify, False)
		self.assertEqual(instance.week_long, False)

	def test_edit_instance_full(self):
		url = "/workshift/instance/{0}/edit/".format(self.instance.pk)
		response = self.client.post(url, {
			"edit": "",
			"title": "Edit Instance Title",
			"description": "I once was from a long line of workshifts",
			"pool": self.instance.pool.pk,
			"start_time": "2:00 PM",
			"end_time": "4:00 PM",
			"date": "05/27/2014",
			"workshifter": self.wp.pk,
			"closed": False,
			"hours": 2,
			"auto_verify": False,
			"week_long": False,
			}, follow=True)
		self.assertRedirects(response, "/workshift/instance/{0}/".format(self.instance.pk))
		self.assertEqual(InstanceInfo.objects.count(), 2)
		instance = WorkshiftInstance.objects.get(pk=self.instance.pk)
		self.assertEqual(instance.weekly_workshift, None)
		self.assertEqual(instance.title, "Edit Instance Title")
		self.assertEqual(instance.description, "I once was from a long line of workshifts")
		self.assertEqual(instance.pool, self.pool)
		self.assertEqual(instance.start_time, time(14, 0, 0))
		self.assertEqual(instance.end_time, time(16, 0, 0))
		self.assertEqual(instance.date, date(2014, 5, 27))
		self.assertEqual(instance.workshifter, self.wp)
		self.assertEqual(instance.closed, False)
		self.assertEqual(instance.hours, 2)
		self.assertEqual(instance.auto_verify, False)
		self.assertEqual(instance.week_long, False)

	def test_delete_instance(self):
		url = "/workshift/instance/{0}/edit/".format(self.instance.pk)
		response = self.client.post(url, {
			"delete": "",
			}, follow=True)
		self.assertRedirects(response, "/workshift/manage/")
		self.assertEqual(WorkshiftType.objects.filter(pk=self.type.pk).count(),
						 1)
		self.assertEqual(RegularWorkshift.objects.filter(pk=self.shift.pk).count(),
						 1)
		self.assertEqual(WorkshiftInstance.objects.filter(pk=self.instance.pk).count(),
						 0)
		self.assertEqual(WorkshiftInstance.objects.filter(pk=self.once.pk).count(),
						 1)

	def test_add_once(self):
		url = "/workshift/manage/add_shift/"
		response = self.client.post(url, {
			"add_instance": "",
			"title": "Add Instance Title",
			"description": "Add Instance Description",
			"pool": self.pool.pk,
			"start_time": "6:00 PM",
			"end_time": "8:00 PM",
			"date": "05/27/2014",
			"workshifter": self.wp.pk,
			"closed": False,
			"hours": 2,
			"auto_verify": False,
			"week_long": False,
			}, follow=True)
		self.assertRedirects(response, "/workshift/manage/")
		instance = WorkshiftInstance.objects.get(pk=self.once.pk + 1)
		self.assertEqual(instance.title, "Add Instance Title")
		self.assertEqual(instance.description, "Add Instance Description")
		self.assertEqual(instance.pool, self.pool)
		self.assertEqual(instance.start_time, time(18, 0, 0))
		self.assertEqual(instance.end_time, time(20, 0, 0))
		self.assertEqual(instance.date, date(2014, 5, 27))
		self.assertEqual(instance.workshifter, self.wp)
		self.assertEqual(instance.closed, False)
		self.assertEqual(instance.hours, 2)
		self.assertEqual(instance.auto_verify, False)
		self.assertEqual(instance.week_long, False)

	def test_edit_once(self):
		url = "/workshift/instance/{0}/edit/".format(self.once.pk)
		response = self.client.post(url, {
			"edit": "",
			"title": "Edit Instance Title",
			"description": "I once was from a long line of workshifts",
			"pool": self.instance.pool.pk,
			"start_time": "2:00 PM",
			"end_time": "4:00 PM",
			"date": "05/27/2014",
			"workshifter": self.wp.pk,
			"closed": False,
			"hours": 2,
			"auto_verify": False,
			"week_long": False,
			}, follow=True)
		self.assertRedirects(response, "/workshift/instance/{0}/".format(self.once.pk))
		self.assertEqual(InstanceInfo.objects.count(), 1)
		instance = WorkshiftInstance.objects.get(pk=self.once.pk)
		self.assertEqual(instance.weekly_workshift, None)
		self.assertEqual(instance.title, "Edit Instance Title")
		self.assertEqual(instance.description, "I once was from a long line of workshifts")
		self.assertEqual(instance.pool, self.pool)
		self.assertEqual(instance.start_time, time(14, 0, 0))
		self.assertEqual(instance.end_time, time(16, 0, 0))
		self.assertEqual(instance.date, date(2014, 5, 27))
		self.assertEqual(instance.workshifter, self.wp)
		self.assertEqual(instance.closed, False)
		self.assertEqual(instance.hours, 2)
		self.assertEqual(instance.auto_verify, False)
		self.assertEqual(instance.week_long, False)

	def test_delete_once(self):
		url = "/workshift/instance/{0}/edit/".format(self.once.pk)
		response = self.client.post(url, {
			"delete": "",
			}, follow=True)
		self.assertRedirects(response, "/workshift/manage/")
		self.assertEqual(WorkshiftType.objects.filter(pk=self.type.pk).count(),
						 1)
		self.assertEqual(RegularWorkshift.objects.filter(pk=self.shift.pk).count(),
						 1)
		self.assertEqual(WorkshiftInstance.objects.filter(pk=self.instance.pk).count(),
						 1)
		self.assertEqual(WorkshiftInstance.objects.filter(pk=self.once.pk).count(),
						 0)

	def test_add_shift(self):
		url = "/workshift/manage/add_shift/"
		response = self.client.post(url, {
			"add_shift": "",
			"workshift_type": self.type.pk,
			"pool": self.pool.pk,
			"title": "IKC",
			"days": [0, 3],
			"hours": 3,
			"count": 2,
			"active": True,
			"current_assignee": self.wp.pk,
			"start_time": "8:00 PM",
			"end_time": "11:00 PM",
			"auto_verify": False,
			"week_long": False,
			"addendum": "IKC needs no addendum.",
			}, follow=True)
		self.assertRedirects(response, "/workshift/manage/")
		shift = RegularWorkshift.objects.get(pk=self.shift.pk + 1)
		self.assertEqual(shift.workshift_type, self.type)
		self.assertEqual(shift.pool, self.pool)
		self.assertEqual(shift.title, "IKC")
		self.assertEqual(shift.days, [0, 3])
		self.assertEqual(shift.hours, 3)
		self.assertEqual(shift.count, 2)
		self.assertEqual(shift.active, True)
		self.assertEqual(shift.current_assignee, self.wp)
		self.assertEqual(shift.start_time, time(20, 0, 0))
		self.assertEqual(shift.end_time, time(23, 0, 0))
		self.assertEqual(shift.auto_verify, False)
		self.assertEqual(shift.week_long, False)
		self.assertEqual(shift.addendum, "IKC needs no addendum.")
		self.assertEqual(2 + 8, WorkshiftInstance.objects.count())

	def test_edit_shift(self):
		url = "/workshift/shift/{0}/edit/".format(self.shift.pk)
		response = self.client.post(url, {
			"edit": "",
			"workshift_type": self.type.pk,
			"pool": self.pool.pk,
			"title": "Edited Title",
			"days": [1, 5],
			"hours": 42,
			"count": 4,
			"active": False,
			"current_assignee": self.up.pk,
			"start_time": "04:00 PM",
			"end_time": "06:00 PM",
			"auto_verify": True,
			"week_long": True,
			"addendum": "Edited addendum",
			}, follow=True)
		self.assertRedirects(response, "/workshift/shift/{0}/".format(self.shift.pk))
		shift = RegularWorkshift.objects.get(pk=self.shift.pk)
		self.assertEqual(shift.workshift_type, self.type)
		self.assertEqual(shift.pool, self.pool)
		self.assertEqual(shift.title, "Edited Title")
		self.assertEqual([], shift.days)
		self.assertEqual(shift.hours, 42)
		self.assertEqual(4, shift.count)
		self.assertEqual(shift.active, False)
		self.assertEqual(shift.current_assignee, self.up)
		self.assertEqual(shift.start_time, time(16, 0, 0))
		self.assertEqual(shift.end_time, time(18, 0, 0))
		self.assertEqual(shift.auto_verify, True)
		self.assertEqual(shift.week_long, True)
		self.assertEqual(shift.addendum, "Edited addendum")

	def test_delete_shift(self):
		url = "/workshift/shift/{0}/edit/".format(self.shift.pk)
		response = self.client.post(url, {
			"delete": "",
			}, follow=True)
		self.assertRedirects(response, "/workshift/manage/")
		self.assertEqual(WorkshiftType.objects.filter(pk=self.type.pk).count(),
						 1)
		self.assertEqual(RegularWorkshift.objects.filter(pk=self.shift.pk).count(),
						 0)
		self.assertEqual(WorkshiftInstance.objects.filter(pk=self.instance.pk).count(),
						 1)
		self.assertEqual(WorkshiftInstance.objects.filter(pk=self.once.pk).count(),
						 1)
		instance = WorkshiftInstance.objects.get(pk=self.instance.pk)
		self.assertEqual(instance.closed, True)
		self.assertEqual(instance.weekly_workshift, None)
		self.assertEqual(instance.title, self.shift.title)
		self.assertEqual(instance.description, self.type.description)
		self.assertEqual(instance.pool, self.shift.pool)
		self.assertEqual(instance.start_time, self.shift.start_time)
		self.assertEqual(instance.end_time, self.shift.end_time)

	def test_add_type(self):
		url = "/workshift/manage/add_shift/"
		response = self.client.post(url, {
			"add_type": "",
			"title": "Added Title",
			"description": "Added Description",
			"quick_tips": "Added Quick Tips",
			"hours": 42,
			"rateable": True,
			}, follow=True)
		self.assertRedirects(response, "/workshift/manage/")
		shift_type = WorkshiftType.objects.get(title="Added Title")
		self.assertEqual(shift_type.title, "Added Title")
		self.assertEqual(shift_type.description, "Added Description")
		self.assertEqual(shift_type.quick_tips, "Added Quick Tips")
		self.assertEqual(shift_type.hours, 42)
		self.assertEqual(shift_type.rateable, True)

	def test_edit_type(self):
		url = "/workshift/type/{0}/edit/".format(self.type.pk)
		response = self.client.post(url, {
			"title": "Edited Title",
			"description": "Edited Description",
			"quick_tips": "Edited Quick Tips",
			"hours": 42,
			"rateable": False,
			}, follow=True)
		self.assertRedirects(response, "/workshift/type/{0}/".format(self.type.pk))
		shift_type = WorkshiftType.objects.get(pk=self.type.pk)
		self.assertEqual(shift_type.title, "Edited Title")
		self.assertEqual(shift_type.description, "Edited Description")
		self.assertEqual(shift_type.quick_tips, "Edited Quick Tips")
		self.assertEqual(shift_type.hours, 42)
		self.assertEqual(shift_type.rateable, False)

class TestSemester(TestCase):
	def setUp(self):
		self.wu = User.objects.create_user(username="wu", password="pwd")
		self.wp = UserProfile.objects.get(user=self.wu)

		self.wm = Manager.objects.create(
			title="Workshift Manager",
			incumbent=self.wp,
			workshift_manager=True,
			)

		self.s1 = Semester.objects.create(
			year=2014, start_date=date.today(),
			end_date=date.today() + timedelta(days=7),
			current=True,
			)

		self.s2 = Semester.objects.create(
			year=2013, start_date=date.today(),
			end_date=date.today() + timedelta(days=7),
			current=False,
			)

		self.wprofile = WorkshiftProfile.objects.create(user=self.wu, semester=self.s1)

		self.client.login(username="wu", password="pwd")

	def test_no_current(self):
		self.s1.current = False
		self.s1.save()

		response = self.client.get("/workshift/", follow=True)
		self.assertRedirects(response, "/workshift/start/")

	def test_multiple_current(self):
		self.s2.current = True
		self.s2.save()

		workshift_emails_str = ""

		response = self.client.get("/workshift/")
		self.assertContains(
			response,
			MESSAGES['MULTIPLE_CURRENT_SEMESTERS'].format(
				admin_email=settings.ADMINS[0][1],
				workshift_emails=workshift_emails_str,
				))

	def test_multiple_current_workshift_email(self):
		self.s2.current = True
		self.s2.save()
		self.wm.email = "devwm@bsc.coop"
		self.wm.save()

		workshift_emails_str = ' (<a href="mailto:{0}">{0}</a>)'.format(self.wm.email)

		response = self.client.get("/workshift/")
		self.assertContains(
			response,
			MESSAGES['MULTIPLE_CURRENT_SEMESTERS'].format(
				admin_email=settings.ADMINS[0][1],
				workshift_emails=workshift_emails_str,
				))

	def test_multiple_current_user_email(self):
		self.s2.current = True
		self.s2.save()
		self.wu.email = "personal@bsc.coop"
		self.wp.email_visible = True
		self.wu.save()
		self.wp.save()

		workshift_emails_str = ' (<a href="mailto:{0}">{0}</a>)'.format(self.wu.email)

		response = self.client.get("/workshift/")
		self.assertContains(
			response,
			MESSAGES['MULTIPLE_CURRENT_SEMESTERS'].format(
				admin_email=settings.ADMINS[0][1],
				workshift_emails=workshift_emails_str,
				))

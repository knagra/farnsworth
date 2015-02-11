
from __future__ import absolute_import

from datetime import timedelta, time, date

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils.timezone import now, localtime

from base.models import User, UserProfile
from managers.models import Manager
from utils.variables import MESSAGES
from workshift.fill import REGULAR_WORKSHIFTS, WEEK_LONG, HUMOR_WORKSHIFTS, \
    BATHROOM_WORKSHIFTS
from workshift.models import *
from workshift.forms import *
from workshift.fields import DAY_CHOICES


class TestPermissions(TestCase):
    """
    Tests that different levels of users and management are only able to access
    the pages they are expected to have permission to.
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

        moment = localtime(now())
        today = moment.date()
        self.sem = Semester.objects.create(
            year=today.year, start_date=today,
            end_date=today + timedelta(days=7),
        )

        self.pool = WorkshiftPool.objects.get(
            semester=self.sem,
        )

        self.hi_pool = WorkshiftPool.objects.create(
            semester=self.sem,
            title="HI Hours",
            hours=4,
            weeks_per_period=0,
        )

        self.wp = WorkshiftProfile.objects.get(user=self.wu)
        self.mp = WorkshiftProfile.objects.get(user=self.mu)
        self.up = WorkshiftProfile.objects.get(user=self.u)
        self.op = WorkshiftProfile.objects.get(user=self.ou)

        self.wtype = WorkshiftType.objects.create(
            title="Test Posts",
        )
        self.mtype = WorkshiftType.objects.create(
            title="Maintenance Cleaning",
        )

        self.wshift = RegularWorkshift.objects.create(
            workshift_type=self.wtype,
            pool=self.pool,
            day=DAY_CHOICES[0][0],
            start_time=moment,
            end_time=moment + timedelta(hours=2),
        )

        self.mshift = RegularWorkshift.objects.create(
            workshift_type=self.mtype,
            pool=self.hi_pool,
            day=DAY_CHOICES[0][0],
            start_time=moment,
            end_time=moment + timedelta(hours=2),
        )

        self.winstance = WorkshiftInstance.objects.create(
            weekly_workshift=self.wshift,
            date=today,
            workshifter=self.up,
        )

        self.minstance = WorkshiftInstance.objects.create(
            weekly_workshift=self.mshift,
            date=today,
            workshifter=self.up,
        )

        info = InstanceInfo.objects.create(
            title="Clean The Deck",
            pool=self.pool,
            description="Make sure to sing sailor tunes.",
        )

        self.wonce = WorkshiftInstance.objects.create(
            info=info,
            date=today,
            workshifter=self.up,
        )

        info = InstanceInfo.objects.create(
            title="Build A Deck",
            pool=self.hi_pool,
            description="Preferably in the shape of a pirate ship.",
        )

        self.monce = WorkshiftInstance.objects.create(
            info=info,
            date=today,
            workshifter=self.up,
        )

    def test_workshift_manager(self):
        self.assertTrue(self.client.login(username="wu", password="pwd"))

        urls = [
            reverse("workshift:start_semester"),
            reverse("workshift:view_semester"),
            reverse("workshift:semester_info"),
            reverse("workshift:profile", kwargs={"targetUsername": self.up.user.username}),
            reverse("workshift:edit_profile", kwargs={"targetUsername": self.up.user.username}),
            reverse("workshift:preferences", kwargs={"targetUsername": self.up.user.username}),
            reverse("workshift:manage"),
            reverse("workshift:fill_shifts"),
            reverse("workshift:assign_shifts"),
            reverse("workshift:adjust_hours"),
            reverse("workshift:add_workshifter"),
            reverse("workshift:fine_date"),
            reverse("workshift:add_shift"),
            reverse("workshift:edit_shift", kwargs={"pk": self.wshift.pk}),
            reverse("workshift:edit_instance", kwargs={"pk": self.winstance.pk}),
            reverse("workshift:edit_type", kwargs={"pk": self.wtype.pk}),
            reverse("workshift:edit_shift", kwargs={"pk": self.mshift.pk}),
            reverse("workshift:edit_instance", kwargs={"pk": self.minstance.pk}),
            reverse("workshift:edit_type", kwargs={"pk": self.mtype.pk}),
        ]
        for url in urls:
            response = self.client.get(url, follow=True)
            self.assertEqual(response.status_code, 200)

    def test_maintenance_manager(self):
        self.assertTrue(self.client.login(username="mu", password="pwd"))

        urls = [
            (False, reverse("workshift:start_semester")),
            (True, reverse("workshift:view_semester")),
            (True, reverse("workshift:semester_info")),
            (True, reverse("workshift:profile", kwargs={"targetUsername": self.up.user.username})),
            (False, reverse("workshift:preferences", kwargs={"targetUsername": self.up.user.username})),
            (True, reverse("workshift:manage")),
            (True, reverse("workshift:fill_shifts")),
            (True, reverse("workshift:assign_shifts")),
            (False, reverse("workshift:adjust_hours")),
            (False, reverse("workshift:add_workshifter")),
            (True, reverse("workshift:add_shift")),
            (True, reverse("workshift:fine_date")),
            (False, reverse("workshift:edit_shift", kwargs={"pk": self.wshift.pk})),
            (False, reverse("workshift:edit_instance", kwargs={"pk": self.winstance.pk})),
            (False, reverse("workshift:edit_type", kwargs={"pk": self.wtype.pk})),
            (True, reverse("workshift:edit_shift", kwargs={"pk": self.mshift.pk})),
            (True, reverse("workshift:edit_instance", kwargs={"pk": self.minstance.pk})),
            (True, reverse("workshift:edit_type", kwargs={"pk": self.mtype.pk})),
        ]
        for okay, url in urls:
            response = self.client.get(url, follow=True)
            if okay:
                self.assertEqual(response.status_code, 200)
            else:
                self.assertRedirects(response, reverse("workshift:view_semester"))
                self.assertContains(response, MESSAGES["ADMINS_ONLY"])

    def test_user(self):
        self.assertTrue(self.client.login(username="u", password="pwd"))

        urls = [
            (False, reverse("workshift:start_semester")),
            (True, reverse("workshift:view_semester")),
            (True, reverse("workshift:semester_info")),
            (True, reverse("workshift:profile", kwargs={"targetUsername": self.up.user.username})),
            (False, reverse("workshift:edit_profile", kwargs={"targetUsername": self.up.user.username})),
            (True, reverse("workshift:preferences", kwargs={"targetUsername": self.up.user.username})),
            (False, reverse("workshift:manage")),
            (False, reverse("workshift:fill_shifts")),
            (False, reverse("workshift:assign_shifts")),
            (False, reverse("workshift:adjust_hours")),
            (False, reverse("workshift:add_workshifter")),
            (False, reverse("workshift:add_shift")),
            (False, reverse("workshift:fine_date")),
            (False, reverse("workshift:edit_shift", kwargs={"pk": self.wshift.pk})),
            (False, reverse("workshift:edit_instance", kwargs={"pk": self.winstance.pk})),
            (False, reverse("workshift:edit_type", kwargs={"pk": self.wtype.pk})),
            (False, reverse("workshift:edit_shift", kwargs={"pk": self.mshift.pk})),
            (False, reverse("workshift:edit_instance", kwargs={"pk": self.minstance.pk})),
            (False, reverse("workshift:edit_type", kwargs={"pk": self.mtype.pk})),
        ]
        for okay, url in urls:
            response = self.client.get(url, follow=True)
            if okay:
                self.assertEqual(response.status_code, 200)
            else:
                self.assertRedirects(response, reverse("workshift:view_semester"))
                self.assertContains(response, MESSAGES["ADMINS_ONLY"])

    def test_other_user(self):
        self.assertTrue(self.client.login(username="ou", password="pwd"))

        urls = [
            (False, reverse("workshift:start_semester")),
            (True, reverse("workshift:view_semester")),
            (True, reverse("workshift:semester_info")),
            (True, reverse("workshift:profile", kwargs={"targetUsername": self.up.user.username})),
            (False, reverse("workshift:edit_profile", kwargs={"targetUsername": self.up.user.username})),
            (False, reverse("workshift:preferences", kwargs={"targetUsername": self.up.user.username})),
            (False, reverse("workshift:manage")),
            (False, reverse("workshift:fill_shifts")),
            (False, reverse("workshift:assign_shifts")),
            (False, reverse("workshift:adjust_hours")),
            (False, reverse("workshift:add_workshifter")),
            (False, reverse("workshift:add_shift")),
            (False, reverse("workshift:fine_date")),
            (False, reverse("workshift:edit_shift", kwargs={"pk": self.wshift.pk})),
            (False, reverse("workshift:edit_instance", kwargs={"pk": self.winstance.pk})),
            (False, reverse("workshift:edit_type", kwargs={"pk": self.wtype.pk})),
            (False, reverse("workshift:edit_shift", kwargs={"pk": self.mshift.pk})),
            (False, reverse("workshift:edit_instance", kwargs={"pk": self.minstance.pk})),
            (False, reverse("workshift:edit_type", kwargs={"pk": self.mtype.pk})),
        ]

        for okay, url in urls:
            response = self.client.get(url, follow=True)
            if okay:
                self.assertEqual(response.status_code, 200)
            else:
                self.assertRedirects(response, reverse("workshift:view_semester"))
                self.assertContains(response, MESSAGES["ADMINS_ONLY"])


class TestStart(TestCase):
    """
    Tests the behavior of the workshift website before any semester has been
    initialized. Also tests that initializing a semester works correctly.
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

        self.assertTrue(self.client.login(username="wu", password="pwd"))

    def test_unauthenticated(self):
        self.client.logout()
        url = reverse("workshift:view_semester")
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, reverse("login") + "?next=" + url)

    def test_before(self):
        url = reverse("workshift:view_semester")
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, reverse("workshift:start_semester"))

        self.client.logout()
        self.assertTrue(self.client.login(username="u", password="pwd"))

        response = self.client.get(url, follow=True)
        self.assertRedirects(response, reverse("homepage"))

    def test_start(self):
        url = reverse("workshift:start_semester")
        response = self.client.post(url, {
            "semester-season": Semester.SUMMER,
            "semester-year": 2014,
            "semester-rate": 13.30,
            "semester-policy": "http://bsc.coop",
            "semester-start_date": date(2014, 5, 22),
            "semester-end_date": date(2014, 8, 15),
        }, follow=True)

        self.assertRedirects(response, reverse("workshift:manage"))

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


class TestViews(TestCase):
    """
    Tests a few basic things about the application: That all the pages can load
    correctly, and that they contain the content that is expected.
    """
    def setUp(self):
        moment = localtime(now())
        today = moment.date()
        self.sem = Semester.objects.create(
            year=today.year,
            start_date=today,
            end_date=today + timedelta(days=6),
        )

        self.u = User.objects.create_user(username="u", password="pwd")
        self.wu = User.objects.create_user(username="wu", password="pwd")
        self.wu.first_name, self.wu.last_name = "Cooperative", "User"
        self.wu.save()

        self.wm = Manager.objects.create(
            title="Workshift Manager",
            incumbent=UserProfile.objects.get(user=self.wu),
            workshift_manager=True,
        )

        self.pool = WorkshiftPool.objects.get(
            semester=self.sem,
            is_primary=True,
        )

        self.wprofile = WorkshiftProfile.objects.get(user=self.wu)

        self.wtype = WorkshiftType.objects.create(
            title="Test Posts",
            description="Test WorkshiftType Description",
            quick_tips="Test Quick Tips",
        )

        self.shift = RegularWorkshift.objects.create(
            workshift_type=self.wtype,
            pool=self.pool,
            day=today.weekday(),
            start_time=moment,
            end_time=moment + timedelta(hours=2),
        )
        self.shift.current_assignees = [self.wprofile]

        self.instance = WorkshiftInstance.objects.get(
            weekly_workshift=self.shift,
        )

        info = InstanceInfo.objects.create(
            title="Test One Time Shift",
            pool=self.pool,
            description="One Time Description",
        )

        self.once = WorkshiftInstance.objects.create(
            info=info,
            date=today + timedelta(days=7),
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

        self.once.logs = [self.sle0, self.sle1, self.sle2, self.sle3, self.sle4]
        self.instance.logs = [self.sle0, self.sle1, self.sle2, self.sle3, self.sle4]

        hours = self.wprofile.pool_hours.get(pool=self.pool)
        hours.first_fine_date = 13.00
        hours.save()

        self.assertTrue(self.client.login(username="wu", password="pwd"))

    def test_no_profile(self):
        self.client.logout()
        self.client.login(username='u', password='pwd')

        urls = [
            reverse("workshift:list_types"),
            reverse("workshift:view_type", kwargs={"pk": self.wtype.pk}),
            reverse("workshift:view_semester"),
            reverse("workshift:profile", kwargs={"targetUsername": self.wprofile.user.username}),
            reverse("workshift:view_shift", kwargs={"pk": self.shift.pk}),
            reverse("workshift:view_instance", kwargs={"pk": self.instance.pk}),
            reverse("workshift:view_instance", kwargs={"pk": self.once.pk}),
            reverse("workshift:view_open"),
            reverse("workshift:semester_info"),
            reverse("workshift:profiles"),
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

    def test_views_load(self):
        urls = [
            reverse("workshift:start_semester"),
            reverse("workshift:list_types"),
            reverse("workshift:view_type", kwargs={"pk": self.wtype.pk}),
            reverse("workshift:edit_type", kwargs={"pk": self.wtype.pk}),
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

        urls = [
            ("workshift:view_semester", {}),
            ("workshift:semester_info", {}),
            ("workshift:profile", {"targetUsername": self.wprofile.user.username}),
            ("workshift:edit_profile", {"targetUsername": self.wprofile.user.username}),
            ("workshift:preferences", {"targetUsername": self.wprofile.user.username}),
            ("workshift:manage", {}),
            ("workshift:fill_shifts", {}),
            ("workshift:assign_shifts", {}),
            ("workshift:add_shift", {}),
            ("workshift:adjust_hours", {}),
            ("workshift:add_workshifter", {}),
            ("workshift:view_shift", {"pk": self.shift.pk}),
            ("workshift:edit_shift", {"pk": self.shift.pk}),
            ("workshift:view_instance", {"pk": self.instance.pk}),
            ("workshift:edit_instance", {"pk": self.instance.pk}),
            ("workshift:view_instance", {"pk": self.once.pk}),
            ("workshift:edit_instance", {"pk": self.once.pk}),
            ("workshift:view_open", {}),
            ("workshift:profiles", {}),
            ("workshift:add_pool", {}),
            ("workshift:view_pool", {"pk": self.pool.pk}),
            ("workshift:edit_pool", {"pk": self.pool.pk}),
        ]
        for name, kwargs in urls:
            url = reverse(name, kwargs=kwargs)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

            kwargs["sem_url"] = "{0}{1}".format(self.sem.season, self.sem.year)
            url = reverse(name, kwargs=kwargs)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

    def test_type_list(self):
        url = reverse("workshift:list_types")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.wtype.title)
        self.assertContains(response, "Week long")
        self.assertNotContains(response, self.wtype.quick_tips)
        self.assertNotContains(response, self.wtype.description)

    def test_type(self):
        url = reverse("workshift:view_type", kwargs={"pk": self.wtype.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.wtype.title)
        self.assertContains(response, self.wtype.quick_tips)
        self.assertContains(response, self.wtype.description)

    def test_type_edit(self):
        url = reverse("workshift:edit_type", kwargs={"pk": self.wtype.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.wtype.title)
        self.assertContains(response, self.wtype.quick_tips)
        self.assertContains(response, self.wtype.description)

    def test_shift(self):
        url = reverse("workshift:view_shift", kwargs={"pk": self.shift.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.wtype.title)
        self.assertContains(response, str(self.shift.hours))
        self.assertContains(response, self.shift.workshift_type.quick_tips)
        self.assertContains(response, self.shift.workshift_type.description)
        for assignee in self.shift.current_assignees.all():
            self.assertContains(response, assignee.user.get_full_name())

    def test_edit_shift(self):
        url = reverse("workshift:edit_shift", kwargs={"pk": self.shift.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.wtype.title)
        self.assertContains(response, str(self.shift.hours))
        for assignee in self.shift.current_assignees.all():
            self.assertContains(response, assignee.user.get_full_name())

    def test_instance(self):
        url = reverse("workshift:view_instance", kwargs={"pk": self.instance.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            self.instance.weekly_workshift.workshift_type.title,
            )
        self.assertContains(
            response,
            self.instance.weekly_workshift.pool.title,
            )
        self.assertContains(response, self.instance.workshifter.user.get_full_name())
        self.assertContains(response, str(self.instance.hours))
        self.assertContains(response, self.sle0.note)
        self.assertContains(response, self.sle1.note)
        self.assertContains(response, self.sle2.note)
        self.assertContains(response, self.sle3.note)
        self.assertContains(response, self.sle4.note)

    def test_edit_instance(self):
        url = reverse("workshift:edit_instance", kwargs={"pk": self.instance.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            self.instance.weekly_workshift.workshift_type.title,
            )
        self.assertContains(
            response,
            self.instance.weekly_workshift.pool.title,
            )
        self.assertContains(
            response,
            str(self.instance.date),
            )
        self.assertContains(
            response,
            self.instance.workshifter.user.get_full_name(),
            )
        self.assertContains(
            response,
            str(self.instance.hours),
            )

    def test_one_time(self):
        url = reverse("workshift:view_instance", kwargs={"pk": self.once.pk})
        response = self.client.get(url)
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
        url = reverse("workshift:edit_instance", kwargs={"pk": self.once.pk})
        response = self.client.get(url)
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
        url = reverse("workshift:view_semester")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_semester_no_prev(self):
        today = self.sem.start_date
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)
        url = reverse("workshift:view_semester")
        response = self.client.get(url + "?day=" + today.strftime("%F"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, today.strftime("%A, %B"))
        self.assertContains(response, today.strftime("%d, %Y"))
        self.assertNotContains(response, "?day=" + yesterday.strftime("%F"))
        self.assertContains(response, "?day=" + tomorrow.strftime("%F"))

    def test_semester_no_next(self):
        today = self.sem.end_date
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)
        url = reverse("workshift:view_semester")
        response = self.client.get(url + "?day=" + today.strftime("%F"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, today.strftime("%A, %B"))
        self.assertContains(response, today.strftime("%d, %Y"))
        self.assertContains(response, "?day=" + yesterday.strftime("%F"))
        self.assertNotContains(response, "?day=" + tomorrow.strftime("%F"))

    def test_semester_bad_day(self):
        url = reverse("workshift:view_semester")

        response = self.client.get(url + "?day=2014")
        self.assertEqual(response.status_code, 200)

        response = self.client.get(url + "?day=abcd")
        self.assertEqual(response.status_code, 200)

        response = self.client.get(url + "?day=2014-20")
        self.assertEqual(response.status_code, 200)

        response = self.client.get(url + "?day=2014-100-100")
        self.assertEqual(response.status_code, 200)

    def test_auto_assign(self):
        self.test_clear_assignees()

        url = reverse("workshift:assign_shifts")
        response = self.client.post(url, {
            "pool": self.pool.pk,
            "auto_assign_shifts": "",
            })
        self.assertRedirects(response, url)
        uprofile = WorkshiftProfile.objects.get(user=self.u)
        self.assertEqual(
            RegularWorkshift.objects.get(pk=self.shift.pk),
            RegularWorkshift.objects.get(current_assignees=uprofile)
            )

    def test_random_assign(self):
        for instance in WorkshiftInstance.objects.all():
            instance.workshifter = None
            instance.save()
        WorkshiftProfile.objects.exclude(pk=self.wprofile.pk).delete()

        url = reverse("workshift:assign_shifts")
        response = self.client.post(url, {
            "pool": self.pool.pk,
            "random_assign_instances": "",
            })
        self.assertRedirects(response, url)
        self.assertEqual(
            1,
            WorkshiftInstance.objects.filter(workshifter=self.wprofile).count()
            )

    def test_clear_assignees(self):
        url = reverse("workshift:assign_shifts")
        response = self.client.post(url, {
            "pool": self.pool.pk,
            "clear_assignments": "",
            })
        self.assertRedirects(response, url)
        self.assertEqual(
            1,
            RegularWorkshift.objects.filter(current_assignees=self.wprofile).count()
        )
        self.assertEqual(
            2, # self.instance, Workshift Manager
            WorkshiftInstance.objects.filter(workshifter=self.wprofile).count(),
        )

    def test_fine_date(self):
        url = reverse("workshift:fine_date")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "workshifters_table",
            )
        self.assertContains(
            response,
            self.pool.title,
            )


class TestPreferences(TestCase):
    """
    Tests the various elements of the workshift preferences page.
    """
    def setUp(self):
        self.wu = User.objects.create_user(username="wu", password="pwd")
        self.wu.first_name, self.wu.last_name = "Cooperative", "User"
        self.wu.save()

        self.wm = Manager.objects.create(
            title="Workshift Manager",
            incumbent=UserProfile.objects.get(user=self.wu),
            workshift_manager=True,
        )

        today = localtime(now()).date()
        self.sem = Semester.objects.create(
            year=today.year, start_date=today,
            end_date=today + timedelta(days=7),
        )

        self.pool = WorkshiftPool.objects.get(
            semester=self.sem,
        )

        self.wprofile = WorkshiftProfile.objects.get(user=self.wu)

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
        self.url = reverse("workshift:preferences", kwargs={"targetUsername": self.wprofile.user.username})

    def test_preferences_get(self):
        response = self.client.get(self.url)
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
            "rating-{}-rating".format(self.w1.pk): WorkshiftRating.LIKE,
            "rating-{}-rating".format(self.w2.pk): WorkshiftRating.DISLIKE,
            "time-0-preference": TimeBlock.BUSY,
            "time-0-day": DAY_CHOICES[0][0], # Monday
            "time-0-start_time": "8:00 AM",
            "time-0-end_time": "5:00 PM",
            "time-1-preference": TimeBlock.BUSY,
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
            "note-note": "Dishes are fun, pots are cathartic.",
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
                [TimeBlock.BUSY, TimeBlock.BUSY, TimeBlock.PREFERRED],
                [DAY_CHOICES[0][0], DAY_CHOICES[-1][0], DAY_CHOICES[1][0]],
                [time(8, 0, 0), time(16, 0, 0), time(18, 0, 0)],
                [time(17, 0, 0), time(21, 0, 0), time(22, 0, 0)],
                ):
            self.assertEqual(block.preference, preference)
            self.assertEqual(block.day, day)
            self.assertEqual(block.start_time, start)
            self.assertEqual(block.end_time, end)

        self.assertEqual(
            "Dishes are fun, pots are cathartic.",
            WorkshiftProfile.objects.get(user=self.wu).note,
        )

    def test_no_note(self):
        response = self.client.post(self.url, {
            "rating-{}-rating".format(self.w1.pk): WorkshiftRating.LIKE,
            "rating-{}-rating".format(self.w2.pk): WorkshiftRating.DISLIKE,
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
            "rating-{}-rating".format(self.w1.pk): WorkshiftRating.LIKE,
            "rating-{}-rating".format(self.w2.pk): WorkshiftRating.DISLIKE,
            "rating-{}-rating".format(w4.pk): WorkshiftRating.LIKE,
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
            "rating-{}-rating".format(self.w1.pk): WorkshiftRating.LIKE,
            "rating-{}-rating".format(self.w2.pk): WorkshiftRating.LIKE,
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
        self.client.post(self.url, {
            "rating-{}-rating".format(self.w1.pk): WorkshiftRating.LIKE,
            "rating-{}-rating".format(self.w2.pk): WorkshiftRating.LIKE,
            "rating-{}-rating".format(self.w3.pk + 1): WorkshiftRating.LIKE,
            "time-TOTAL_FORMS": 0,
            "time-INITIAL_FORMS": 0,
            "time-MAX_NUM_FORMS": 50,
        })

        self.assertEqual(self.wprofile.ratings.count(), 2)

    def test_unrateable(self):
        """
        Ensure that users cannot rate unrateable shifts.
        """
        self.client.post(self.url, {
            "rating-{}-rating".format(self.w1.pk): WorkshiftRating.LIKE,
            "rating-{}-rating".format(self.w2.pk): WorkshiftRating.LIKE,
            "rating-{}-rating".format(self.w3.pk): WorkshiftRating.LIKE,
            "time-TOTAL_FORMS": 0,
            "time-INITIAL_FORMS": 0,
            "time-MAX_NUM_FORMS": 50,
        })

        self.assertEqual(self.wprofile.ratings.count(), 2)


class TestWorkshifts(TestCase):
    """
    Tests the pages for adding and modifying workshift types, regular shifts,
    and instances of shifts.
    """
    def setUp(self):
        self.wu = User.objects.create_user(username="wu", password="pwd")
        self.u = User.objects.create_user(username="u", password="pwd")

        self.wm = Manager.objects.create(
            title="Workshift Manager",
            incumbent=UserProfile.objects.get(user=self.wu),
            workshift_manager=True,
        )

        today = localtime(now()).date()
        self.sem = Semester.objects.create(
            year=2014,
            start_date=today,
            end_date=today + timedelta(days=6),
        )
        self.pool = WorkshiftPool.objects.get(
            semester=self.sem,
        )

        self.wp = WorkshiftProfile.objects.get(user=self.wu)
        self.up = WorkshiftProfile.objects.get(user=self.u)

        self.wtype = WorkshiftType.objects.create(
            title="Test Posts",
            description="Test Description",
        )

        self.shift = RegularWorkshift.objects.create(
            workshift_type=self.wtype,
            pool=self.pool,
            day=today.weekday(),
            start_time=time(16),
            end_time=time(18),
        )

        self.instance = WorkshiftInstance.objects.get(
            weekly_workshift=self.shift,
        )

        info = InstanceInfo.objects.create(
            title="Clean The Deck",
            pool=self.pool,
            description="Make sure to sing sailor tunes.",
        )

        self.once = WorkshiftInstance.objects.create(
            info=info,
            date=today,
            workshifter=self.wp,
        )

        self.client.login(username="wu", password="pwd")

    def test_add_instance(self):
        url = reverse("workshift:add_shift")
        response = self.client.post(url, {
            "add_instance": "",
            "weekly_workshift": self.shift.pk,
            "date": date(2014, 5, 27),
            "workshifter": self.wp.pk,
            "closed": False,
            "hours": 2,
            }, follow=True)

        self.assertRedirects(response, reverse("workshift:manage"))
        instance = WorkshiftInstance.objects.get(pk=self.once.pk + 1)
        self.assertEqual(self.shift, instance.weekly_workshift)
        self.assertEqual(None, instance.info)
        self.assertEqual(date(2014, 5, 27), instance.date)
        self.assertEqual(self.wp, instance.workshifter)
        self.assertEqual(False, instance.closed)
        self.assertEqual(2, instance.hours)
        self.assertEqual(self.shift.verify, instance.verify)
        self.assertEqual(False, instance.week_long)

    def test_edit_instance(self):
        url = reverse("workshift:edit_instance", kwargs={"pk": self.instance.pk})
        response = self.client.post(url, {
            "edit": "",
            "weekly_workshift": self.instance.weekly_workshift.pk,
            "title": self.instance.title,
            "description": self.instance.description,
            "pool": self.instance.pool.pk,
            "start_time": self.instance.start_time.strftime("%I:%M %p"),
            "end_time": self.instance.end_time.strftime("%I:%M %p"),
            "date": date(2014, 5, 27),
            "workshifter": self.wp.pk,
            "closed": False,
            "verify": self.instance.verify,
            "week_long": self.instance.week_long,
            }, follow=True)

        url = reverse("workshift:view_instance", kwargs={"pk": self.instance.pk})
        self.assertRedirects(response, url)
        self.assertEqual(1, InstanceInfo.objects.count())
        instance = WorkshiftInstance.objects.get(pk=self.instance.pk)
        self.assertEqual(self.instance.weekly_workshift, instance.weekly_workshift)
        self.assertEqual(self.instance.title, instance.title)
        self.assertEqual(self.instance.description, instance.description)
        self.assertEqual(self.pool, instance.pool)
        self.assertEqual(self.instance.start_time, instance.start_time)
        self.assertEqual(self.instance.end_time, instance.end_time)
        self.assertEqual(date(2014, 5, 27), instance.date)
        self.assertEqual(self.wp, instance.workshifter)
        self.assertEqual(False, instance.closed)
        self.assertEqual(self.instance.verify, instance.verify)
        self.assertEqual(self.instance.week_long, instance.week_long)

    def test_edit_instance_full(self):
        url = reverse("workshift:edit_instance", kwargs={"pk": self.instance.pk})
        response = self.client.post(url, {
            "edit": "",
            "title": "Edit Instance Title",
            "description": "I once was from a long line of workshifts",
            "pool": self.instance.pool.pk,
            "start_time": "2:00 PM",
            "end_time": "4:00 PM",
            "date": date(2014, 5, 27),
            "workshifter": self.wp.pk,
            "closed": False,
            "verify": SELF_VERIFY,
            "week_long": False,
            }, follow=True)

        url = reverse("workshift:view_instance", kwargs={"pk": self.instance.pk})
        self.assertRedirects(response, url)
        self.assertEqual(InstanceInfo.objects.count(), 2)
        instance = WorkshiftInstance.objects.get(pk=self.instance.pk)
        self.assertEqual(instance.weekly_workshift, None)
        self.assertEqual(instance.title, "Edit Instance Title")
        self.assertEqual(
            "I once was from a long line of workshifts",
            instance.description,
            )
        self.assertEqual(instance.pool, self.pool)
        self.assertEqual(instance.start_time, time(14, 0, 0))
        self.assertEqual(instance.end_time, time(16, 0, 0))
        self.assertEqual(instance.date, date(2014, 5, 27))
        self.assertEqual(instance.workshifter, self.wp)
        self.assertEqual(instance.closed, False)
        self.assertEqual(SELF_VERIFY, instance.verify)
        self.assertEqual(instance.week_long, False)

    def test_delete_instance(self):
        url = reverse("workshift:edit_instance", kwargs={"pk": self.instance.pk})
        response = self.client.post(url, {
            "delete": "",
            }, follow=True)

        self.assertRedirects(response, reverse("workshift:manage"))
        self.assertEqual(
            1,
            WorkshiftType.objects.filter(pk=self.wtype.pk).count(),
            )
        self.assertEqual(
            1,
            RegularWorkshift.objects.filter(pk=self.shift.pk).count(),
            )
        self.assertEqual(
            0,
            WorkshiftInstance.objects.filter(pk=self.instance.pk).count(),
            )
        self.assertEqual(
            1,
            WorkshiftInstance.objects.filter(pk=self.once.pk).count(),
            )

    def test_add_once(self):
        url = reverse("workshift:add_shift")
        response = self.client.post(url, {
            "add_instance": "",
            "title": "Add Instance Title",
            "description": "Add Instance Description",
            "pool": self.pool.pk,
            "start_time": "6:00 PM",
            "end_time": "8:00 PM",
            "date": date(2014, 5, 27),
            "workshifter": self.wp.pk,
            "closed": False,
            "hours": 2,
            "verify": WORKSHIFT_MANAGER_VERIFY,
            "week_long": False,
            }, follow=True)

        self.assertRedirects(response, reverse("workshift:manage"))
        instance = WorkshiftInstance.objects.get(pk=self.once.pk + 1)
        self.assertEqual("Add Instance Title", instance.title)
        self.assertEqual("Add Instance Description", instance.description)
        self.assertEqual(self.pool, instance.pool)
        self.assertEqual(time(18, 0, 0), instance.start_time)
        self.assertEqual(time(20, 0, 0), instance.end_time)
        self.assertEqual(date(2014, 5, 27), instance.date)
        self.assertEqual(self.wp, instance.workshifter)
        self.assertEqual(False, instance.closed)
        self.assertEqual(2, instance.hours)
        self.assertEqual(WORKSHIFT_MANAGER_VERIFY, instance.verify)
        self.assertEqual(False, instance.week_long)

    def test_edit_once(self):
        url = reverse("workshift:edit_instance", kwargs={"pk": self.once.pk})
        response = self.client.post(url, {
            "edit": "",
            "title": "Edit Instance Title",
            "description": "I once was from a long line of workshifts",
            "pool": self.instance.pool.pk,
            "start_time": "2:00 PM",
            "end_time": "4:00 PM",
            "date": date(2014, 5, 27),
            "workshifter": self.wp.pk,
            "closed": False,
            "verify": OTHER_VERIFY,
            "week_long": False,
            }, follow=True)

        url = reverse("workshift:view_instance", kwargs={"pk": self.once.pk})
        self.assertRedirects(response, url)
        self.assertEqual(1, InstanceInfo.objects.count())
        instance = WorkshiftInstance.objects.get(pk=self.once.pk)
        self.assertEqual(None, instance.weekly_workshift)
        self.assertEqual("Edit Instance Title", instance.title)
        self.assertEqual(
            "I once was from a long line of workshifts",
            instance.description,
            )
        self.assertEqual(self.pool, instance.pool)
        self.assertEqual(time(14, 0, 0), instance.start_time)
        self.assertEqual(time(16, 0, 0), instance.end_time)
        self.assertEqual(date(2014, 5, 27), instance.date)
        self.assertEqual(self.wp, instance.workshifter)
        self.assertEqual(False, instance.closed)
        self.assertEqual(OTHER_VERIFY, instance.verify)
        self.assertEqual(False, instance.week_long)

    def test_delete_once(self):
        url = reverse("workshift:edit_instance", kwargs={"pk": self.once.pk})
        response = self.client.post(url, {
            "delete": "",
            }, follow=True)

        self.assertRedirects(response, reverse("workshift:manage"))
        self.assertEqual(
            1,
            WorkshiftType.objects.filter(pk=self.wtype.pk).count(),
            )
        self.assertEqual(
            1,
            RegularWorkshift.objects.filter(pk=self.shift.pk).count(),
            )
        self.assertEqual(
            WorkshiftInstance.objects.filter(pk=self.instance.pk).count(),
            1,
            )
        self.assertEqual(
            0,
            WorkshiftInstance.objects.filter(pk=self.once.pk).count(),
            )

    def test_edit_shift(self):
        url = reverse("workshift:edit_shift", kwargs={"pk": self.shift.pk})
        response = self.client.post(url, {
            "edit": "",
            "workshift_type": self.wtype.pk,
            "pool": self.pool.pk,
            "hours": 42,
            "count": 4,
            "day": DAY_CHOICES[0][0],
            "active": True,
            "current_assignees": [self.up.pk],
            "start_time": "4:00 PM",
            "end_time": "6:00 PM",
            "verify": AUTO_VERIFY,
            "addendum": "Edited addendum",
        }, follow=True)

        url = reverse("workshift:view_shift", kwargs={"pk": self.shift.pk})
        self.assertRedirects(response, url)

        shift = RegularWorkshift.objects.get(pk=self.shift.pk)
        self.assertEqual(self.wtype, shift.workshift_type)
        self.assertEqual(self.pool, shift.pool)
        self.assertEqual(shift.hours, 42)
        self.assertEqual(4, shift.count)
        self.assertEqual(True, shift.active)
        self.assertEqual(
            [self.up],
            list(shift.current_assignees.all()),
        )
        instances = WorkshiftInstance.objects.filter(weekly_workshift=shift)
        self.assertGreater(instances.count(), 0)
        self.assertTrue(all(i.workshifter == self.up for i in instances))
        self.assertEqual(time(16), shift.start_time)
        self.assertEqual(time(18), shift.end_time)
        self.assertEqual(AUTO_VERIFY, shift.verify)
        self.assertEqual(DAY_CHOICES[0][0], shift.day)
        self.assertEqual(False, shift.week_long)
        self.assertEqual("Edited addendum", shift.addendum)

    def test_delete_shift(self):
        url = reverse("workshift:edit_shift", kwargs={"pk": self.shift.pk})
        response = self.client.post(url, {
            "delete": "",
            }, follow=True)

        self.assertRedirects(response, reverse("workshift:manage"))
        self.assertEqual(
            1,
            WorkshiftType.objects.filter(pk=self.wtype.pk).count(),
            )
        self.assertEqual(
            0,
            RegularWorkshift.objects.filter(pk=self.shift.pk).count(),
            )
        self.assertEqual(
            0,
            WorkshiftInstance.objects.filter(pk=self.instance.pk).count(),
            )
        self.assertEqual(
            1,
            WorkshiftInstance.objects.filter(pk=self.once.pk).count(),
            )

    def test_add_type(self):
        url = reverse("workshift:add_shift")
        response = self.client.post(url, {
            "add_type": "",
            "type-title": "Added Title",
            "type-description": "Added Description",
            "type-quick_tips": "Added Quick Tips",
            "type-rateable": True,
            "type-assignment": WorkshiftType.AUTO_ASSIGN,
            "shifts-TOTAL_FORMS": 0,
            "shifts-INITIAL_FORMS": 0,
            "shifts-MAX_NUM_FORMS": 50,
            }, follow=True)
        self.assertRedirects(response, reverse("workshift:manage"))
        shift_type = WorkshiftType.objects.get(title="Added Title")
        self.assertEqual(shift_type.title, "Added Title")
        self.assertEqual(shift_type.description, "Added Description")
        self.assertEqual(shift_type.quick_tips, "Added Quick Tips")
        self.assertEqual(shift_type.rateable, True)
        self.assertEqual(shift_type.assignment, WorkshiftType.AUTO_ASSIGN)

    def test_edit_type(self):
        url = reverse("workshift:edit_type", kwargs={"pk": self.wtype.pk})
        response = self.client.post(url, {
            "edit": "",
            "edit-title": "Edited Title",
            "edit-description": "Edited Description",
            "edit-quick_tips": "Edited Quick Tips",
            "edit-rateable": False,
            "edit-assignment": WorkshiftType.MANUAL_ASSIGN,
            "shifts-TOTAL_FORMS": 0,
            "shifts-INITIAL_FORMS": 0,
            "shifts-MAX_NUM_FORMS": 50,
            }, follow=True)

        url = reverse("workshift:view_type", kwargs={"pk": self.wtype.pk})
        self.assertRedirects(response, url)
        shift_type = WorkshiftType.objects.get(pk=self.wtype.pk)
        self.assertEqual(shift_type.title, "Edited Title")
        self.assertEqual(shift_type.description, "Edited Description")
        self.assertEqual(shift_type.quick_tips, "Edited Quick Tips")
        self.assertEqual(shift_type.rateable, False)
        self.assertEqual(shift_type.assignment, WorkshiftType.MANUAL_ASSIGN)


class TestSemester(TestCase):
    """
    Tests for correct behavior when multiple semesters exist, including when
    there exist multiple "current" semesters.
    """
    def setUp(self):
        self.wu = User.objects.create_user(username="wu", password="pwd")
        self.wu.first_name = "Workshift"
        self.wu.last_name = "User"
        self.wu.save()
        self.wp = UserProfile.objects.get(user=self.wu)

        self.wm = Manager.objects.create(
            title="Workshift Manager",
            incumbent=self.wp,
            workshift_manager=True,
        )

        today = localtime(now()).date()
        last_year = today - timedelta(days=365)
        self.s2 = Semester.objects.create(
            year=last_year.year,
            start_date=last_year,
            end_date=last_year + timedelta(days=7),
        )

        self.s1 = Semester.objects.create(
            year=today.year, start_date=today,
            end_date=today + timedelta(days=7),
        )

        self.assertEqual(
            RegularWorkshift.objects.count(),
            2,
        )

        self.wprofile = WorkshiftProfile.objects.get(user=self.wu, semester=self.s1)

        self.client.login(username="wu", password="pwd")

    def test_fill_shifts(self):
        url = reverse("workshift:fill_shifts")
        response = self.client.post(url, {
        }, follow=True)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            RegularWorkshift.objects.count(),
            2, # 2x Workshift Manager
        )

        names = [
            "fill_regular_shifts",
            "fill_humor_shifts",
            "fill_bathroom_shifts",
            "fill_social_shifts",
            "fill_HI_shifts",
        ]
        for name in names:
            response = self.client.post(url, {
                name: "",
            }, follow=True)

            self.assertRedirects(response, reverse("workshift:fill_shifts"))

        # Check we created the correct number of shifts (no duplicates across semesters)
        self.assertEqual(
            RegularWorkshift.objects.count(),
            sum(len(i[2]) for i in REGULAR_WORKSHIFTS) + len(WEEK_LONG) +
            sum(len(i[2]) for i in HUMOR_WORKSHIFTS) +
            sum(len(i[2]) for i in BATHROOM_WORKSHIFTS) +
            Manager.objects.count() * 2,
        )

        response = self.client.post(url, {
            "reset_all_shifts": "",
        }, follow=True)

        self.assertRedirects(response, reverse("workshift:fill_shifts"))

        self.assertEqual(
            RegularWorkshift.objects.count(),
            2, # 2x Workshift Manager
        )

    def test_clear_semester(self):
        self.s1.delete()
        self.assertEqual(
            Semester.objects.count(),
            1,
        )

        self.s2.delete()
        self.assertEqual(
            Semester.objects.count(),
            0,
        )

    def test_new_semester(self):
        url = reverse("workshift:start_semester")
        today = localtime(now()).date()
        response = self.client.post(url, {
            "semester-year": today.year,
            "semester-season": Semester.FALL,
            "semester-rate": 14.00,
            "semester-policy": "http://bsc.coop",
            "semester-start_date": today,
            "semester-end_date": today + timedelta(weeks=18) - timedelta(days=today.weekday()),
        }, follow=True)

        self.assertRedirects(response, reverse("workshift:manage"))
        self.assertEqual(
            Semester.objects.filter(current=True).count(),
            1,
        )
        s = Semester.objects.get(current=True)
        self.assertEqual(
            s.year,
            today.year,
        )
        self.assertEqual(
            s.season,
            Semester.FALL,
        )
        self.assertEqual(
            WorkshiftProfile.objects.filter(semester=s).count(),
            1,
        )
        self.assertEqual(
            RegularWorkshift.objects.filter(pool__semester=s).count(),
            1,
        )
        self.assertEqual(
            WorkshiftProfile.objects.filter(user=self.wu, semester=s).count(),
            1,
        )
        shift = RegularWorkshift.objects.get(pool__semester=s)
        self.assertEqual(
            [i.pk for i in shift.current_assignees.all()],
            [i.pk for i in WorkshiftProfile.objects.filter(user=self.wu, semester=s)],
        )
        self.assertEqual(
            WorkshiftInstance.objects.filter(weekly_workshift=shift).count(),
            18, # 18 instances of Workshift Manager shift
        )

    def test_no_current(self):
        self.s1.current = False
        self.s1.save()

        url = reverse("workshift:view_semester")
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, reverse("workshift:start_semester"))

    def test_multiple_current(self):
        self.s2.current = True
        self.s2.save()

        workshift_emails_str = ""

        url = reverse("workshift:view_semester")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
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

        url = reverse("workshift:view_semester")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
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

        url = reverse("workshift:view_semester")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            MESSAGES['MULTIPLE_CURRENT_SEMESTERS'].format(
                admin_email=settings.ADMINS[0][1],
                workshift_emails=workshift_emails_str,
                ))

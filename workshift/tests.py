
from __future__ import absolute_import

from datetime import timedelta, time, date

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils.timezone import now

from base.models import User, UserProfile, ProfileRequest
from farnsworth import pre_fill
from managers.models import Manager
from utils.variables import MESSAGES
from workshift.models import *
from workshift.forms import *
from workshift.fields import DAY_CHOICES
from workshift.cron import CollectBlownCronJob, UpdateWeeklyStandings
from workshift import utils

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

class TestAssignment(TestCase):
    """
    Test the functionality of workshift.utils.auto_assign_shifts. This should
    include respecting member's shift preferences and schedules.
    """
    def setUp(self):
        self.u = User.objects.create_user(username="u0")
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
            is_primary=True,
            semester=self.semester,
            )
        self.p2 = WorkshiftPool.objects.create(
            title="Alternate Workshift",
            semester=self.semester,
            )
        self.wtype1 = WorkshiftType.objects.create(
            title="Like Type",
            )
        self.wtype2 = WorkshiftType.objects.create(
            title="Indifferent Type",
            )
        self.wtype3 = WorkshiftType.objects.create(
            title="Dislike Type",
            )
        preference1 = WorkshiftRating.objects.create(
            rating=WorkshiftRating.LIKE,
            workshift_type=self.wtype1,
            )
        preference2 = WorkshiftRating.objects.create(
            rating=WorkshiftRating.INDIFFERENT,
            workshift_type=self.wtype2,
            )
        preference3 = WorkshiftRating.objects.create(
            rating=WorkshiftRating.DISLIKE,
            workshift_type=self.wtype3,
            )
        self.profile.ratings = [preference1, preference2, preference3]
        self.profile.save()
        utils.make_workshift_pool_hours(semester=self.semester)

    def test_auto_assign_one(self):
        """
        Assign one shift to a member.
        """
        shift1 = RegularWorkshift.objects.create(
            workshift_type=self.wtype1,
            pool=self.p1,
            hours=5,
            )
        unfinished = utils.auto_assign_shifts(self.semester)
        self.assertEqual([], unfinished)
        self.assertIn(self.profile, shift1.current_assignees.all())

    def test_pre_assigned(self):
        """
        Test that assignment behaves correctly when members are already assigned
        to other workshifts.
        """
        shift1 = RegularWorkshift.objects.create(
            workshift_type=self.wtype1,
            pool=self.p1,
            hours=5,
            )
        shift2 = RegularWorkshift.objects.create(
            workshift_type=self.wtype3,
            pool=self.p1,
            hours=1,
            )
        shift2.current_assignees = [self.profile]
        shift2.save()
        unfinished = utils.auto_assign_shifts(self.semester)
        self.assertEqual([self.profile], unfinished)
        self.assertNotIn(self.profile, shift1.current_assignees.all())

    def test_auto_assign_one_overflow(self):
        """
        Don't assign one shift to a member because it pushes them over their
        weekly requirement.
        """
        shift1 = RegularWorkshift.objects.create(
            workshift_type=self.wtype1,
            pool=self.p1,
            hours=6,
            )
        unfinished = utils.auto_assign_shifts(self.semester)
        self.assertEqual([self.profile], unfinished)
        self.assertNotIn(self.profile, shift1.current_assignees.all())

    def test_auto_assign_two(self):
        """
        Assign two shifts to a member.
        """
        shift1 = RegularWorkshift.objects.create(
            workshift_type=self.wtype1,
            pool=self.p1,
            hours=2,
            )
        shift2 = RegularWorkshift.objects.create(
            workshift_type=self.wtype1,
            pool=self.p1,
            hours=3,
            )
        unfinished = utils.auto_assign_shifts(self.semester)
        self.assertEqual([], unfinished)
        self.assertIn(self.profile, shift1.current_assignees.all())
        self.assertIn(self.profile, shift2.current_assignees.all())

    def test_auto_assign_two_preferred(self):
        """
        Assign two shifts to a member.
        """
        shift1 = RegularWorkshift.objects.create(
            workshift_type=self.wtype1,
            pool=self.p1,
            hours=5,
            )
        shift2 = RegularWorkshift.objects.create(
            workshift_type=self.wtype2,
            pool=self.p1,
            hours=5,
            )
        unfinished = utils.auto_assign_shifts(self.semester)
        self.assertEqual([], unfinished)
        self.assertIn(self.profile, shift1.current_assignees.all())
        self.assertNotIn(self.profile, shift2.current_assignees.all())

    def test_auto_assign_two_overflow(self):
        """
        Assign a preferred shift to a member, but don't assign the other because
        it pushes them over their weekly requirement.
        """
        shift1 = RegularWorkshift.objects.create(
            workshift_type=self.wtype1,
            pool=self.p1,
            hours=3,
            )
        shift2 = RegularWorkshift.objects.create(
            workshift_type=self.wtype2,
            pool=self.p1,
            hours=3,
            )
        unfinished = utils.auto_assign_shifts(self.semester)
        self.assertEqual([self.profile], unfinished)
        self.assertIn(self.profile, shift1.current_assignees.all())
        self.assertNotIn(self.profile, shift2.current_assignees.all())

    def _test_auto_assign_fifty(self):
        """
        Assign fifty members to fifty shifts, with each shift providing 5 hours
        of workshift. Ensures that the assignments don't mysteriously break or
        run for an extremely long time for medium-sized houses.
        """
        shifts = []
        for i in range(50):
            shifts.append(
                RegularWorkshift.objects.create(
                    workshift_type=self.wtype1,
                    pool=self.p1,
                    hours=5,
                    )
                )
        for i in range(1, 50):
            user = User.objects.create_user(username="u{0}".format(i))

        utils.make_workshift_pool_hours(semester=self.semester)
        unfinished = utils.auto_assign_shifts(self.semester)
        self.assertEqual([], unfinished)
        for shift in shifts:
            self.assertEqual(1, shift.current_assignees.count())

    def _test_auto_assign_one_hundred_and_fifty(self):
        """
        Assign 150 members to 150 shifts, with each shift providing 5 hours
        of workshift. Ensures that the assignments don't mysteriously break or
        run for an extremely long time for large houses.
        """
        shifts = []
        for i in range(150):
            shifts.append(
                RegularWorkshift.objects.create(
                    workshift_type=self.wtype1,
                    pool=self.p1,
                    hours=5,
                    )
                )
        for i in range(1, 150):
            user = User.objects.create_user(username="u{0}".format(i))

        utils.make_workshift_pool_hours(semester=self.semester)
        unfinished = utils.auto_assign_shifts(self.semester)
        self.assertEqual([], unfinished)
        for shift in shifts:
            self.assertEqual(1, shift.current_assignees.count())

    def test_pre_fill_and_assign(self):
        """
        Tests that shifts can be correctly assigned after farnsworth/pre_fill.py
        is run. This is a good test of how the assignment code functions "in the
        wild," rather than with many duplicates of the same shift.
        """
        users = []
        for i in range(1, 50):
            users.append(User.objects.create_user(username="u{0}".format(i)))
        pre_fill.main(["--managers", "--workshift"])
        utils.make_workshift_pool_hours(semester=self.semester)
        # Assign manager shifts beforehand
        for user, manager in zip(users, Manager.objects.all()):
            manager.incumbent = UserProfile.objects.get(user=user)
            manager.save()
        unfinished = utils.auto_assign_shifts(self.semester)
        self.assertEqual([], unfinished)

    def _test_pre_fill_and_assign_humor(self):
        """
        Tests that humor shifts can be correctly assigned after
        farnsworth/pre_fill.py is run.
        """
        for i in range(1, 50):
            user = User.objects.create_user(username="u{0}".format(i))
        pre_fill.main(["--managers", "--workshift"])
        utils.make_workshift_pool_hours(semester=self.semester)
        # Assign manager shifts beforehand
        manager_shifts = RegularWorkshift.objects.filter(
            pool=self.p1, workshift_type__auto_assign=False,
            )
        profiles = WorkshiftProfile.objects.all()
        for profile, shift in zip(profiles, manager_shifts):
            shift.current_assignees.add(profile)
            shift.save()
        unfinished = utils.auto_assign_shifts(
            self.semester, pool=WorkshiftPool.objects.get(title="Humor Shift")
            )
        self.assertEqual([], unfinished)

class TestUtils(TestCase):
    """
    Tests most of the various functions within workshift.utils.
    """
    def setUp(self):
        self.semester = Semester.objects.create(
            year=2014,
            season=Semester.SUMMER,
            start_date=date(2014, 5, 25),
            end_date=date(2014, 8, 16),
            )
        self.u = User.objects.create_user(username="u")
        self.profile = WorkshiftProfile.objects.get(user=self.u)
        self.p1 = WorkshiftPool.objects.create(
            is_primary=True,
            semester=self.semester,
            sign_out_cutoff=24,
            verify_cutoff=2,
            )
        self.p2 = WorkshiftPool.objects.create(
            title="Alternate Workshift",
            semester=self.semester,
            )

    def test_cron_blown(self):
        CollectBlownCronJob().do()

    def test_cron_standings(self):
        UpdateWeeklyStandings().do()

    def test_get_year_season(self):
        year, season = utils.get_year_season()
        self.assertLess(abs(year - now().date().year), 2)
        self.assertIn(season, [Semester.SPRING, Semester.SUMMER, Semester.FALL])

    def test_starting_month(self):
        # Starting in Summer, Fall, and Spring
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
        PoolHours.objects.all().delete()
        utils.make_workshift_pool_hours()
        self.assertEqual(2, PoolHours.objects.count())
        self.assertEqual(2, self.profile.pool_hours.count())

    def test_make_pool_hours_profile(self):
        PoolHours.objects.all().delete()
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
        PoolHours.objects.all().delete()
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
        PoolHours.objects.all().delete()
        utils.make_workshift_pool_hours(
            semester=self.semester,
            primary_hours=6,
            )
        self.assertEqual(6, PoolHours.objects.get(pool=self.p1).hours)
        self.assertEqual(self.p2.hours, PoolHours.objects.get(pool=self.p2).hours)

    def test_can_manage(self):
        pass

    def test_is_available(self):
        pass

    def test_make_instances(self):
        wtype = WorkshiftType.objects.create(
            title="Test Make Instances",
            )
        # Disconnect the handler and run make_instances ourselves
        models.signals.post_save.disconnect(
            create_workshift_instances, sender=RegularWorkshift
            )
        shift = RegularWorkshift.objects.create(
            workshift_type=wtype,
            pool=self.p1,
            day=4,
            hours=7,
            )
        shift.current_assignees = [self.profile]
        shift.save()
        today = now().date()
        WorkshiftInstance.objects.create(
            weekly_workshift=shift,
            date=today - timedelta(today.weekday()),
            )
        instances = utils.make_instances(
            semester=self.semester,
            shifts=[shift],
            )

        for instance in instances:
            self.assertEqual(wtype.title, instance.title)
            self.assertEqual(shift, instance.weekly_workshift)
            self.assertEqual(shift.hours, instance.hours)
            self.assertEqual(shift.hours, instance.intended_hours)
            self.assertEqual(1, instance.logs.count())

        self.assertEqual(
            set([shift.day]),
            set(i.date.weekday() for i in instances),
            )

    def test_collect_blown(self):
        utils.make_workshift_pool_hours()
        self.assertEqual(
            ([], [], []),
            utils.collect_blown(),
            )

        self.assertEqual(
            ([], [], []),
            utils.collect_blown(semester=self.semester),
            )

        moment = now().replace(hour=20, minute=0, second=0, microsecond=0)
        past = moment - timedelta(days=1)

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
            date=moment.date(),
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
                end_time=moment.time(),
                pool=self.p1,
                ),
            date=moment.date(),
            semester=self.semester,
            )
        edge_datetime = moment - timedelta(hours=self.p1.verify_cutoff, minutes=1)
        edge_case_2 = WorkshiftInstance.objects.create(
            info=InstanceInfo.objects.create(
                title="Edge Case 2: Closed",
                end_time=edge_datetime.time(),
                pool=self.p1,
                ),
            date=edge_datetime.date(),
            )
        signed_out_1 = WorkshiftInstance.objects.create(
            info=InstanceInfo.objects.create(
                title="Workshifter signed out early enough",
                pool=self.p1,
                ),
            date=past.date(),
            semester=self.semester,
            )
        signed_out_2 = WorkshiftInstance.objects.create(
            info=InstanceInfo.objects.create(
                title="Workshifter signed out too late",
                pool=self.p1,
                ),
            liable=self.profile,
            date=past.date(),
            semester=self.semester,
            )
        self.assertEqual(
            ([to_close, edge_case_2, signed_out_1], [], [blown, signed_out_2]),
            utils.collect_blown(moment=moment),
            )

class TestViews(TestCase):
    """
    Tests a few basic things about the application: That all the pages can load
    correctly, and that they contain the content that is expected.
    """
    def setUp(self):
        today = now().date()
        self.sem = Semester.objects.create(
            year=2014, start_date=today,
            end_date=today + timedelta(days=7),
            current=True,
            )

        self.u = User.objects.create_user(username="u", password="pwd")
        self.wu = User.objects.create_user(username="wu", password="pwd")
        self.wu.first_name, self.wu.last_name = "Cooperative", "User"
        self.wu.save()

        self.pool = WorkshiftPool.objects.create(
            semester=self.sem,
            is_primary=True,
            )

        self.wm = Manager.objects.create(
            title="Workshift Manager",
            incumbent=UserProfile.objects.get(user=self.wu),
            workshift_manager=True,
            )

        self.pool.managers = [self.wm]
        self.pool.save()

        self.wprofile = WorkshiftProfile.objects.get(user=self.wu)

        self.wtype = WorkshiftType.objects.create(
            title="Test Posts",
            description="Test WorkshiftType Description",
            quick_tips="Test Quick Tips",
            )

        self.shift = RegularWorkshift.objects.create(
            workshift_type=self.wtype,
            pool=self.pool,
            start_time=now(),
            end_time=now() + timedelta(hours=2),
            )
        self.shift.current_assignees = [self.wprofile]
        self.shift.days = [DAY_CHOICES[0][0]]
        self.shift.save()

        self.instance = WorkshiftInstance.objects.create(
            weekly_workshift=self.shift,
            date=today,
            workshifter=self.wprofile,
            )

        self.open_instance = WorkshiftInstance.objects.create(
            weekly_workshift=self.shift,
            date=today,
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
            ("workshift:profile", {"targetUsername": self.wprofile.user.username}),
            ("workshift:edit_profile", {"targetUsername": self.wprofile.user.username}),
            ("workshift:preferences", {"targetUsername": self.wprofile.user.username}),
            ("workshift:manage", {}),
            ("workshift:fill_shifts", {}),
            ("workshift:assign_shifts", {}),
            ("workshift:add_shift", {}),
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
            2,
            WorkshiftInstance.objects.filter(workshifter=self.wprofile).count()
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
        today = now().date()
        self.sem = Semester.objects.create(
            year=2014, start_date=today,
            end_date=today + timedelta(days=7),
            current=True,
            )

        self.wu = User.objects.create_user(username="wu", password="pwd")
        self.wu.first_name, self.wu.last_name = "Cooperative", "User"
        self.wu.save()

        self.wm = Manager.objects.create(
            title="Workshift Manager",
            incumbent=UserProfile.objects.get(user=self.wu),
            workshift_manager=True,
            )

        self.pool = WorkshiftPool.objects.create(
            semester=self.sem,
            )
        self.pool.managers = [self.wm]
        self.pool.save()

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
            "rating-1-rating": WorkshiftRating.LIKE,
            "rating-2-rating": WorkshiftRating.DISLIKE,
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
    """
    Tests the functionality of the buttons for marking shifts as blown,
    verifying shifts, signing in and out of shifts at appropriate times, etc.
    """
    def setUp(self):
        today = now().date()
        self.sem = Semester.objects.create(
            year=2014, start_date=today,
            end_date=today + timedelta(days=7),
            current=True,
            )

        self.wu = User.objects.create_user(username="wu", password="pwd")
        self.u = User.objects.create_user(username="u", password="pwd")
        self.ou = User.objects.create_user(username="ou", password="pwd")

        self.wm = Manager.objects.create(
            title="Workshift Manager",
            incumbent=UserProfile.objects.get(user=self.wu),
            workshift_manager=True,
            )

        self.pool = WorkshiftPool.objects.create(
            semester=self.sem,
            any_blown=True,
            )
        self.pool.managers = [self.wm]

        self.wp = WorkshiftProfile.objects.get(user=self.wu)
        self.up = WorkshiftProfile.objects.get(user=self.u)
        self.op = WorkshiftProfile.objects.get(user=self.ou)

        utils.make_workshift_pool_hours(semester=self.sem, profiles=[self.up])

        self.wtype = WorkshiftType.objects.create(
            title="Test Posts",
            description="Test WorkshiftType Description",
            quick_tips="Test Quick Tips",
            )

        self.shift = RegularWorkshift.objects.create(
            workshift_type=self.wtype,
            pool=self.pool,
            start_time=now(),
            end_time=time(23, 59, 59),
            )
        self.shift.days = [DAY_CHOICES[0][0]]
        self.shift.save()

        self.instance = WorkshiftInstance.objects.create(
            weekly_workshift=self.shift,
            date=today,
            workshifter=self.up,
            verify=OTHER_VERIFY,
            )

        info = InstanceInfo.objects.create(
            title="Test One Time Shift",
            pool=self.pool,
            )

        self.once = WorkshiftInstance.objects.create(
            info=info,
            date=today,
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

        form = VerifyShiftForm({"pk": self.instance.pk}, profile=self.wp)
        form.is_valid()
        self.assertTrue(form.is_valid())
        self.assertIsInstance(form.save(), WorkshiftInstance)
        log = self.instance.logs.filter(entry_type=ShiftLogEntry.VERIFY)
        self.assertEqual(1, log.count())
        self.assertEqual(log[0].person, self.wp)

        form = VerifyShiftForm({"pk": self.once.pk}, profile=self.wp)
        self.assertFalse(form.is_valid())
        self.assertIn("Workshift is not filled.", form.errors["pk"])

    def test_no_self_verify(self):
        self.pool.save()

        self.assertTrue(self.client.login(username="u", password="pwd"))

        form = VerifyShiftForm({"pk": self.instance.pk}, profile=self.up)
        self.assertFalse(form.is_valid())
        self.assertIn("Workshifter cannot verify self.", form.errors["pk"])

        self.assertTrue(self.client.login(username="ou", password="pwd"))

        form = VerifyShiftForm({"pk": self.instance.pk}, profile=self.op)
        form.is_valid()
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
        self.assertEqual(["Not signed into workshift."], form.errors["pk"])

    def test_missing_shift(self):
        self.assertTrue(self.client.login(username="u", password="pwd"))

        form = SignOutForm({"pk": -1}, profile=self.up)
        self.assertFalse(form.is_valid())

        form = SignOutForm({"pk": 100}, profile=self.up)
        self.assertFalse(form.is_valid())

        form = SignOutForm({"pk": "a"}, profile=self.up)
        self.assertFalse(form.is_valid())

    def test_closed_shift(self):
        self.once.closed = True
        self.once.save()
        form = SignOutForm({"pk": self.once.pk}, profile=self.up)
        self.assertFalse(form.is_valid())

class TestPermissions(TestCase):
    """
    Tests that different levels of users and management are only able to access
    the pages they are expected to have permission to.
    """
    def setUp(self):
        today = now().date()
        self.sem = Semester.objects.create(
            year=2014, start_date=today,
            end_date=today + timedelta(days=7),
            current=True,
            )

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

        self.pool = WorkshiftPool.objects.create(
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
            start_time=now(),
            end_time=now() + timedelta(hours=2),
            )
        self.wshift.day = DAY_CHOICES[0][0]
        self.wshift.save()

        self.mshift = RegularWorkshift.objects.create(
            workshift_type=self.mtype,
            pool=self.hi_pool,
            start_time=now(),
            end_time=now() + timedelta(hours=2),
            )
        self.mshift.days = [DAY_CHOICES[0][0]]
        self.mshift.save()

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
            reverse("workshift:profile", kwargs={"targetUsername": self.up.user.username}),
            reverse("workshift:edit_profile", kwargs={"targetUsername": self.up.user.username}),
            reverse("workshift:preferences", kwargs={"targetUsername": self.up.user.username}),
            reverse("workshift:manage"),
            reverse("workshift:fill_shifts"),
            reverse("workshift:assign_shifts"),
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
            (True, reverse("workshift:profile", kwargs={"targetUsername": self.up.user.username})),
            (False, reverse("workshift:preferences", kwargs={"targetUsername": self.up.user.username})),
            (True, reverse("workshift:manage")),
            (True, reverse("workshift:fill_shifts")),
            (True, reverse("workshift:assign_shifts")),
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
            (True, reverse("workshift:profile", kwargs={"targetUsername": self.up.user.username})),
            (False, reverse("workshift:edit_profile", kwargs={"targetUsername": self.up.user.username})),
            (True, reverse("workshift:preferences", kwargs={"targetUsername": self.up.user.username})),
            (False, reverse("workshift:manage")),
            (False, reverse("workshift:fill_shifts")),
            (False, reverse("workshift:assign_shifts")),
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
            (True, reverse("workshift:profile", kwargs={"targetUsername": self.up.user.username})),
            (False, reverse("workshift:edit_profile", kwargs={"targetUsername": self.up.user.username})),
            (False, reverse("workshift:preferences", kwargs={"targetUsername": self.up.user.username})),
            (False, reverse("workshift:manage")),
            (False, reverse("workshift:fill_shifts")),
            (False, reverse("workshift:assign_shifts")),
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

class TestWorkshifters(TestCase):
    """
    Tests that workshift profiles are created correctly for different types of
    members.
    """
    def setUp(self):
        self.ru = User.objects.create_user(username="ru", password="pwd")
        self.bu = User.objects.create_user(username="bu", password="pwd")
        self.au = User.objects.create_user(username="au", password="pwd")

        self.ru.is_superuser = True
        self.ru.save()

        self.rp = UserProfile.objects.get(user=self.ru)
        self.bp = UserProfile.objects.get(user=self.bu)
        self.ap = UserProfile.objects.get(user=self.au)

        self.rp.status = UserProfile.RESIDENT
        self.bp.status = UserProfile.BOARDER
        self.ap.status = UserProfile.ALUMNUS

        self.rp.save()
        self.bp.save()
        self.ap.save()

        Manager.objects.create(
            title="Workshift Manager",
            incumbent=UserProfile.objects.get(user=self.ru),
            workshift_manager=True,
            )

        self.assertTrue(self.client.login(username="ru", password="pwd"))

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

    def test_no_alumni(self):
        """
        Tests that WorkshiftProfiles are not created for alumni.
        """
        self.assertEqual(
            1,
            WorkshiftProfile.objects.filter(user=self.ru).count(),
            )
        self.assertEqual(
            0,
            WorkshiftProfile.objects.filter(user=self.bu).count(),
            )
        self.assertEqual(
            0,
            WorkshiftProfile.objects.filter(user=self.au).count(),
            )

    def test_add_user_resident(self):
        """
        Test that adding a resident creates a workshift profile.
        """
        pr = ProfileRequest.objects.create(
            username="request",
            first_name="first",
            last_name="last",
            email="pr@email.com",
            affiliation=UserProfile.RESIDENT,
            password="pwd",
            )

        url = reverse("modify_profile_request", kwargs={"request_pk": pr.pk})
        response = self.client.post(url, {
            "username": pr.username,
            "first_name": pr.first_name,
            "last_name": pr.last_name,
            "email": pr.email,
            "affiliation": pr.affiliation,
            "former_houses": "",
            "is_active": True,
            "add_user": "",
            }, follow=True)

        self.assertRedirects(response, reverse("manage_profile_requests"))
        self.assertContains(
            response,
            "User {0} was successfully added".format(pr.username),
            )

        self.assertEqual(
            1,
            WorkshiftProfile.objects.filter(user__username=pr.username).count(),
            )

    def test_add_user_boarder(self):
        """
        Test that adding a boarder creates a workshift profile.
        """
        pr = ProfileRequest.objects.create(
            username="request",
            first_name="first",
            last_name="last",
            email="pr@email.com",
            affiliation=UserProfile.BOARDER,
            password="pwd",
            )

        url = reverse("modify_profile_request", kwargs={"request_pk": pr.pk})
        response = self.client.post(url, {
            "username": pr.username,
            "first_name": pr.first_name,
            "last_name": pr.last_name,
            "email": pr.email,
            "affiliation": pr.affiliation,
            "former_houses": "",
            "is_active": True,
            "add_user": "",
            }, follow=True)

        self.assertRedirects(response, reverse("manage_profile_requests"))
        self.assertContains(
            response,
            "User {0} was successfully added".format(pr.username),
            )

        self.assertEqual(
            0,
            WorkshiftProfile.objects.filter(user__username=pr.username).count(),
            )

    def test_add_user_alumni(self):
        """
        Test that adding an alumni does not create a workshift profile.
        """
        pr = ProfileRequest.objects.create(
            username="request",
            first_name="first",
            last_name="last",
            email="pr@email.com",
            affiliation=UserProfile.ALUMNUS,
            password="pwd",
            )

        url = reverse("modify_profile_request", kwargs={"request_pk": pr.pk})
        response = self.client.post(url, {
            "username": pr.username,
            "first_name": pr.first_name,
            "last_name": pr.last_name,
            "email": pr.email,
            "affiliation": pr.affiliation,
            "former_houses": "",
            "is_active": True,
            "add_user": "",
            }, follow=True)

        self.assertRedirects(response, reverse("manage_profile_requests"))
        self.assertContains(
            response,
            "User {0} was successfully added".format(pr.username),
            )

        self.assertEqual(
            0,
            WorkshiftProfile.objects.filter(user__username=pr.username).count(),
            )

    def test_add_workshifter(self):
        url = reverse("workshift:add_workshifter")
        response = self.client.post(url, {
            "user-{0}-add_profile".format(self.bu.pk): True,
            "user-{0}-hours".format(self.bu.pk): 3,
            "user-{0}-hours".format(self.au.pk): 3,
            })

        self.assertRedirects(response, reverse("workshift:manage"))
        self.assertEqual(
            1,
            WorkshiftProfile.objects.filter(user=self.bu).count()
            )
        self.assertEqual(
            0,
            WorkshiftProfile.objects.filter(user=self.au).count()
            )
        profile = WorkshiftProfile.objects.get(user=self.bu)
        self.assertEqual(
            profile.pool_hours.get(
                pool=WorkshiftPool.objects.get(is_primary=True),
                ).hours,
            3,
            )

class TestWorkshifts(TestCase):
    """
    Tests the pages for adding and modifying workshift types, regular shifts,
    and instances of shifts.
    """
    def setUp(self):
        today = now().date()
        self.sem = Semester.objects.create(
            year=2014, start_date=today,
            end_date=today + timedelta(days=7),
            current=True,
            )
        self.pool = WorkshiftPool.objects.create(
            semester=self.sem,
            )

        self.wu = User.objects.create_user(username="wu", password="pwd")
        self.u = User.objects.create_user(username="u", password="pwd")

        self.wm = Manager.objects.create(
            title="Workshift Manager",
            incumbent=UserProfile.objects.get(user=self.wu),
            workshift_manager=True,
            )

        self.pool.managers = [self.wm]
        self.pool.save()

        self.wp = WorkshiftProfile.objects.get(user=self.wu)
        self.up = WorkshiftProfile.objects.get(user=self.u)

        self.type = WorkshiftType.objects.create(
            title="Test Posts",
            description="Test Description",
            )

        self.shift = RegularWorkshift.objects.create(
            workshift_type=self.type,
            pool=self.pool,
            start_time=time(16, 0, 0),
            end_time=time(18, 0, 0)
            )
        self.shift.days = [DAY_CHOICES[0][0]]
        self.shift.save()

        self.instance = WorkshiftInstance.objects.create(
            weekly_workshift=self.shift,
            date=today,
            workshifter=self.wp,
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
            WorkshiftType.objects.filter(pk=self.type.pk).count(),
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
            WorkshiftType.objects.filter(pk=self.type.pk).count(),
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
            "workshift_type": self.type.pk,
            "pool": self.pool.pk,
            "day": 6,
            "hours": 42,
            "count": 4,
            "active": False,
            "current_assignees": [self.up.pk],
            "start_time": "4:00 PM",
            "end_time": "6:00 PM",
            "verify": AUTO_VERIFY,
            "week_long": True,
            "addendum": "Edited addendum",
            }, follow=True)

        url = reverse("workshift:view_shift", kwargs={"pk": self.shift.pk})
        self.assertRedirects(response, url)

        shift = RegularWorkshift.objects.get(pk=self.shift.pk)
        self.assertEqual(self.type, shift.workshift_type)
        self.assertEqual(self.pool, shift.pool)
        self.assertEqual(6, shift.day)
        self.assertEqual(shift.hours, 42)
        self.assertEqual(4, shift.count)
        self.assertEqual(False, shift.active)
        self.assertEqual(
            [self.up],
            list(shift.current_assignees.all()),
            )
        self.assertEqual(time(16, 0, 0), shift.start_time)
        self.assertEqual(time(18, 0, 0), shift.end_time)
        self.assertEqual(AUTO_VERIFY, shift.verify)
        self.assertEqual(True, shift.week_long)
        self.assertEqual("Edited addendum", shift.addendum)

    def test_delete_shift(self):
        url = reverse("workshift:edit_shift", kwargs={"pk": self.shift.pk})
        response = self.client.post(url, {
            "delete": "",
            }, follow=True)

        self.assertRedirects(response, reverse("workshift:manage"))
        self.assertEqual(
            1,
            WorkshiftType.objects.filter(pk=self.type.pk).count(),
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
        url = reverse("workshift:edit_type", kwargs={"pk": self.type.pk})
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

        url = reverse("workshift:view_type", kwargs={"pk": self.type.pk})
        self.assertRedirects(response, url)
        shift_type = WorkshiftType.objects.get(pk=self.type.pk)
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
        today = now().date()
        self.s1 = Semester.objects.create(
            year=2014, start_date=today,
            end_date=today + timedelta(days=7),
            current=True,
            )

        self.wu = User.objects.create_user(username="wu", password="pwd")
        self.wp = UserProfile.objects.get(user=self.wu)

        self.wm = Manager.objects.create(
            title="Workshift Manager",
            incumbent=self.wp,
            workshift_manager=True,
            )

        self.s2 = Semester.objects.create(
            year=2013, start_date=today,
            end_date=today + timedelta(days=7),
            current=False,
            )

        self.wprofile = WorkshiftProfile.objects.get(user=self.wu, semester=self.s1)

        self.client.login(username="wu", password="pwd")

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

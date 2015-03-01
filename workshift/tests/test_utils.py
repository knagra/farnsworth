
from __future__ import absolute_import

from datetime import time, date, timedelta

from django.test import TestCase
from django.utils.timezone import now, localtime

from farnsworth import pre_fill
from workshift.models import *
from workshift.forms import *
from workshift.cron import CollectBlownCronJob, UpdateWeeklyStandings
from workshift import utils, signals


class TestUtils(TestCase):
    """
    Tests most of the various functions within workshift.utils.
    """
    def setUp(self):
        self.u = User.objects.create_user(
            username="u", first_name="N", last_name="M",
        )

        today = localtime(now()).date()
        self.semester = Semester.objects.create(
            year=today.year,
            season=Semester.SUMMER,
            start_date=today,
            end_date=today + timedelta(weeks=18),
        )
        self.profile = WorkshiftProfile.objects.get(user=self.u)
        self.p1 = WorkshiftPool.objects.get(
            is_primary=True,
            semester=self.semester,
        )
        self.p1.sign_out_cutoff = 24
        self.p1.verify_cutoff = 2
        self.p1.save()

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
        self.assertLess(abs(year - localtime(now()).date().year), 2)
        self.assertIn(
            season,
            [Semester.SPRING, Semester.SUMMER, Semester.FALL],
        )

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
        self.assertEqual(
            6,
            PoolHours.objects.get(pool=self.p1).hours,
        )
        self.assertEqual(
            self.p2.hours,
            PoolHours.objects.get(pool=self.p2).hours,
        )

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
            signals.create_workshift_instances, sender=RegularWorkshift
        )

        shift = RegularWorkshift.objects.create(
            workshift_type=wtype,
            pool=self.p1,
            day=4,
            hours=7,
        )

        shift.current_assignees = [self.profile]

        today = localtime(now()).date()
        WorkshiftInstance.objects.create(
            weekly_workshift=shift,
            date=today - timedelta(today.weekday()),
        )
        instances = utils.make_instances(
            semester=self.semester,
            shifts=[shift],
        )

        models.signals.post_save.connect(
            signals.create_workshift_instances, sender=RegularWorkshift
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

        moment = localtime(now().replace(
            hour=20, minute=0, second=0, microsecond=0,
        ))
        past = moment - timedelta(days=1)

        WorkshiftInstance.objects.create(
            info=InstanceInfo.objects.create(
                title="Closed",
                pool=self.p1,
                end_time=time(12),
            ),
            closed=True,
            date=past.date(),
            semester=self.semester,
        )
        to_close = WorkshiftInstance.objects.create(
            info=InstanceInfo.objects.create(
                title="To be closed",
                pool=self.p1,
                end_time=time(12),
            ),
            date=past.date(),
            semester=self.semester,
        )
        WorkshiftInstance.objects.create(
            info=InstanceInfo.objects.create(
                title="Not Blown",
                pool=self.p1,
                end_time=time(12),
            ),
            date=moment.date(),
            semester=self.semester,
        )
        blown = WorkshiftInstance.objects.create(
            info=InstanceInfo.objects.create(
                title="Blown",
                pool=self.p1,
                end_time=time(12),
            ),
            date=past.date(),
            workshifter=self.profile,
            semester=self.semester,
        )
        WorkshiftInstance.objects.create(
            info=InstanceInfo.objects.create(
                title="Edge Case 1: Not Closed",
                pool=self.p1,
                end_time=moment.time(),
            ),
            date=moment.date(),
            semester=self.semester,
        )
        edge_datetime = moment - timedelta(
            hours=self.p1.verify_cutoff, minutes=1,
        )
        edge_case_2 = WorkshiftInstance.objects.create(
            info=InstanceInfo.objects.create(
                title="Edge Case 2: Closed",
                pool=self.p1,
                end_time=edge_datetime.time(),
            ),
            date=edge_datetime.date(),
        )
        signed_out_1 = WorkshiftInstance.objects.create(
            info=InstanceInfo.objects.create(
                title="Workshifter signed out early enough",
                pool=self.p1,
                end_time=time(12),
            ),
            date=past.date(),
            semester=self.semester,
        )
        signed_out_2 = WorkshiftInstance.objects.create(
            info=InstanceInfo.objects.create(
                title="Workshifter signed out too late",
                pool=self.p1,
                end_time=time(12),
            ),
            liable=self.profile,
            date=past.date(),
            semester=self.semester,
        )
        self.assertEqual(
            ([to_close, edge_case_2, signed_out_1], [], [blown, signed_out_2]),
            utils.collect_blown(moment=moment),
        )


class TestAssignment(TestCase):
    """
    Test the functionality of workshift.utils.auto_assign_shifts. This should
    include respecting member's shift preferences and schedules.
    """
    def setUp(self):
        self.u = User.objects.create_user(username="u0")
        today = localtime(now()).date()
        self.semester = Semester.objects.create(
            year=today.year,
            start_date=today,
            end_date=today + timedelta(days=6),
        )
        self.profile = WorkshiftProfile.objects.get(
            user=self.u,
            semester=self.semester,
        )
        self.p1 = WorkshiftPool.objects.get(
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

        instances = WorkshiftInstance.objects.filter(weekly_workshift=shift1)
        self.assertGreater(instances.count(), 0)
        self.assertTrue(all(
            instance.workshifter == self.profile
            for instance in instances
        ))

        pool_hours = self.profile.pool_hours.get(pool=self.p1)
        self.assertEqual(
            pool_hours.assigned_hours,
            pool_hours.hours,
        )

    def test_pre_assigned(self):
        """
        Test that assignment behaves correctly when members are already
        assigned to other workshifts.
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

        unfinished = utils.auto_assign_shifts(self.semester)
        self.assertEqual([self.profile], unfinished)
        self.assertNotIn(self.profile, shift1.current_assignees.all())

        pool_hours = self.profile.pool_hours.get(pool=self.p1)
        self.assertEqual(
            pool_hours.assigned_hours,
            1,
        )

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

        instances = WorkshiftInstance.objects.filter(weekly_workshift=shift1)
        self.assertGreater(instances.count(), 0)
        self.assertTrue(all(
            instance.workshifter is None
            for instance in instances
        ))

        pool_hours = self.profile.pool_hours.get(pool=self.p1)
        self.assertEqual(
            pool_hours.assigned_hours,
            0,
        )

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

        for shift in [shift1, shift2]:
            instances = WorkshiftInstance.objects.filter(
                weekly_workshift=shift,
            )
            self.assertGreater(instances.count(), 0)
            self.assertTrue(all(
                instance.workshifter == self.profile
                for instance in instances
            ))

        pool_hours = self.profile.pool_hours.get(pool=self.p1)
        self.assertEqual(
            pool_hours.assigned_hours,
            pool_hours.hours,
        )

    def test_auto_assign_two_preferred(self):
        """
        Assign one of two shifts to a member.
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

        instances = WorkshiftInstance.objects.filter(weekly_workshift=shift1)
        self.assertGreater(instances.count(), 0)
        self.assertTrue(all(
            instance.workshifter == self.profile
            for instance in instances
        ))

        instances = WorkshiftInstance.objects.filter(weekly_workshift=shift2)
        self.assertGreater(instances.count(), 0)
        self.assertTrue(all(
            instance.workshifter is None
            for instance in instances
        ))

        pool_hours = self.profile.pool_hours.get(pool=self.p1)
        self.assertEqual(
            pool_hours.assigned_hours,
            pool_hours.hours,
        )

    def test_auto_assign_two_overflow(self):
        """
        Assign a preferred shift to a member, but don't assign the other
        because it pushes them over their weekly requirement.
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

        instances = WorkshiftInstance.objects.filter(weekly_workshift=shift1)
        self.assertGreater(instances.count(), 0)
        self.assertTrue(all(
            instance.workshifter == self.profile
            for instance in instances
        ))

        instances = WorkshiftInstance.objects.filter(weekly_workshift=shift2)
        self.assertGreater(instances.count(), 0)
        self.assertTrue(all(
            instance.workshifter is None
            for instance in instances
        ))

        pool_hours = self.profile.pool_hours.get(pool=self.p1)
        self.assertEqual(
            pool_hours.assigned_hours,
            3,
        )

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
            User.objects.create_user(username="u{0}".format(i))

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
            User.objects.create_user(username="u{0}".format(i))

        utils.make_workshift_pool_hours(semester=self.semester)
        unfinished = utils.auto_assign_shifts(self.semester)
        self.assertEqual([], unfinished)
        for shift in shifts:
            self.assertEqual(1, shift.current_assignees.count())

    def test_pre_fill_and_assign(self):
        """
        Tests that shifts can be correctly assigned after
        farnsworth/pre_fill.py is run. This is a good test of how the
        assignment code functions "in the wild," rather than with many
        duplicates of the same shift.
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
            User.objects.create_user(username="u{0}".format(i))
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

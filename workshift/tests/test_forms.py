
from __future__ import absolute_import

from datetime import time, timedelta

from django.test import TestCase
from django.utils.timezone import now, localtime

from managers.models import Manager
from workshift.models import *
from workshift.forms import *
from workshift.fields import DAY_CHOICES


class TestInteractForms(TestCase):
    """
    Tests the functionality of the buttons for marking shifts as blown,
    verifying shifts, signing in and out of shifts at appropriate times, etc.
    """
    def setUp(self):
        self.wu = User.objects.create_user(username="wu", password="pwd")
        self.u = User.objects.create_user(username="u", password="pwd")
        self.ou = User.objects.create_user(username="ou", password="pwd")

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
        self.pool.any_blown = True
        self.pool.save()

        self.wp = WorkshiftProfile.objects.get(user=self.wu)
        self.up = WorkshiftProfile.objects.get(user=self.u)
        self.op = WorkshiftProfile.objects.get(user=self.ou)

        self.wtype = WorkshiftType.objects.create(
            title="Test Posts",
            description="Test WorkshiftType Description",
            quick_tips="Test Quick Tips",
        )

        self.shift = RegularWorkshift.objects.create(
            workshift_type=self.wtype,
            pool=self.pool,
            day=DAY_CHOICES[0][0],
            start_time=localtime(now()),
            end_time=time(23, 59, 59),
        )

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

    def test_verify(self):
        self.assertTrue(self.client.login(username="u", password="pwd"))

        form = VerifyShiftForm({"pk": self.instance.pk}, profile=self.wp)
        self.assertTrue(form.is_valid())
        self.assertIsInstance(form.save(), WorkshiftInstance)

        log = self.instance.logs.filter(entry_type=ShiftLogEntry.VERIFY)
        self.assertEqual(1, log.count())
        self.assertEqual(log[0].person, self.wp)

    def test_unverify(self):
        self.test_verify()

        form = UndoShiftForm({"pk": self.instance.pk}, profile=self.wp)
        self.assertTrue(form.is_valid())
        self.assertIsInstance(form.save(), WorkshiftInstance)

        log = self.instance.logs.filter(entry_type=ShiftLogEntry.UNVERIFY)
        self.assertEqual(1, log.count())
        self.assertEqual(log[0].person, self.wp)

    def test_unfilled(self):
        self.assertTrue(self.client.login(username="u", password="pwd"))

        form = VerifyShiftForm({"pk": self.once.pk}, profile=self.wp)
        self.assertFalse(form.is_valid())
        self.assertIn("Workshift is not filled.", form.errors["pk"])

    def test_no_self_verify(self):
        self.pool.save()

        self.assertTrue(self.client.login(username="u", password="pwd"))

        form = VerifyShiftForm({"pk": self.instance.pk}, profile=self.up)
        self.assertFalse(form.is_valid())
        self.assertIn("Workshifter cannot verify self.", form.errors["pk"])

        self.client.logout()
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

    def test_blown(self):
        self.assertTrue(self.client.login(username="wu", password="pwd"))

        form = BlownShiftForm({"pk": self.instance.pk}, profile=self.wp)
        self.assertTrue(form.is_valid())
        self.assertIsInstance(form.save(), WorkshiftInstance)

        log = self.instance.logs.filter(entry_type=ShiftLogEntry.BLOWN)
        self.assertEqual(1, log.count())
        self.assertEqual(log[0].person, self.wp)

    def test_unblown(self):
        self.test_blown()

        form = UndoShiftForm({"pk": self.instance.pk}, profile=self.wp)
        self.assertTrue(form.is_valid())
        self.assertIsInstance(form.save(), WorkshiftInstance)

        log = self.instance.logs.filter(entry_type=ShiftLogEntry.UNBLOWN)
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
        self.assertEqual(["Workshift does not exist."], form.errors["pk"])

        form = SignOutForm({"pk": 100}, profile=self.up)
        self.assertFalse(form.is_valid())
        self.assertEqual(["Workshift does not exist."], form.errors["pk"])

        form = SignOutForm({"pk": "a"}, profile=self.up)
        self.assertFalse(form.is_valid())
        self.assertEqual(["Enter a whole number."], form.errors["pk"])

    def test_closed_shift(self):
        self.once.closed = True
        self.once.save()

        form = SignOutForm({"pk": self.once.pk}, profile=self.up)
        self.assertFalse(form.is_valid())
        self.assertEqual(["Workshift has been closed."], form.errors["pk"])

    def test_edit_hours(self):
        form = EditHoursForm(
            {
                "hours": self.once.hours + 1,
                "note": "Better than expected",
            },
            instance=self.once,
            profile=self.wp,
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.save(), self.once)
        self.assertEqual(self.once.intended_hours, self.once.hours - 1)

        log = self.once.logs.filter(entry_type=ShiftLogEntry.MODIFY_HOURS)
        self.assertEqual(1, log.count())
        self.assertEqual(log[0].person, self.wp)

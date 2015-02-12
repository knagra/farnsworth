
from __future__ import absolute_import

from datetime import timedelta

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils.timezone import now, localtime

from base.models import User, UserProfile, ProfileRequest
from managers.models import Manager
from workshift.models import *


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
        today = localtime(now()).date()
        response = self.client.post(url, {
            "semester-season": Semester.SUMMER,
            "semester-year": today.year,
            "semester-rate": 13.30,
            "semester-policy": "http://bsc.coop",
            "semester-start_date": today,
            "semester-end_date": today + timedelta(weeks=18),
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

class TestMakeInstances(TestCase):
    def setUp(self):
        self.u = User.objects.create_user(username="u", password="pwd")
        self.wu = User.objects.create_user(username="wu", password="pwd")
        self.wu.first_name, self.wu.last_name = "Cooperative", "User"
        self.wu.save()

        self.today = localtime(now())
        self.semester = Semester.objects.create(
            year=self.today.year,
            start_date=self.today,
            end_date=self.today + timedelta(days=13),
        )

        self.pool = WorkshiftPool.objects.get(
            semester=self.semester,
            is_primary=True,
        )

        self.wtype = WorkshiftType.objects.create(
            title="Test Posts",
        )


    def test_make_instances(self):
        shift = RegularWorkshift.objects.create(
            workshift_type=self.wtype,
            pool=self.pool,
            day=self.today.weekday(),
        )

        self.assertEqual(
            WorkshiftInstance.objects.filter(
                weekly_workshift=shift,
            ).count(),
            2,
        )


    def test_make_instances_inactive(self):
        shift = RegularWorkshift.objects.create(
            workshift_type=self.wtype,
            pool=self.pool,
            day=self.today.weekday(),
            active=False,
        )

        self.assertEqual(
            WorkshiftInstance.objects.filter(
                weekly_workshift=shift,
            ).count(),
            0,
        )


    def test_switch_active(self):
        shift = RegularWorkshift.objects.create(
            workshift_type=self.wtype,
            pool=self.pool,
            day=self.today.weekday(),
            active=False,
        )

        self.assertEqual(
            WorkshiftInstance.objects.filter(
                weekly_workshift=shift,
            ).count(),
            0,
        )

        shift.active = True
        shift.save()

        self.assertEqual(
            WorkshiftInstance.objects.filter(
                weekly_workshift=shift,
            ).count(),
            2,
        )


    def test_switch_inactive(self):
        shift = RegularWorkshift.objects.create(
            workshift_type=self.wtype,
            pool=self.pool,
            day=self.today.weekday(),
        )

        self.assertEqual(
            WorkshiftInstance.objects.filter(
                weekly_workshift=shift,
            ).count(),
            2,
        )

        shift.active = False
        shift.save()

        self.assertEqual(
            WorkshiftInstance.objects.filter(
                weekly_workshift=shift,
            ).count(),
            0,
        )

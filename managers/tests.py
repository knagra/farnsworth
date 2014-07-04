"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.contrib.auth.models import User
from django.test import TestCase
from django.test.utils import override_settings
from django.core.urlresolvers import reverse

from datetime import datetime

from utils.variables import ANONYMOUS_USERNAME, MESSAGES
from utils.funcs import convert_to_url
from base.models import UserProfile, ProfileRequest
from managers.models import Manager, RequestType, Request, Response, Announcement

class TestPermissions(TestCase):
    def setUp(self):
        self.u = User.objects.create_user(username="u", password="pwd")
        self.st = User.objects.create_user(username="st", password="pwd")
        self.pu = User.objects.create_user(username="pu", password="pwd")
        self.su = User.objects.create_user(username="su", password="pwd")
        self.np = User.objects.create_user(username="np", password="pwd")

        self.st.is_staff = True
        self.su.is_staff, self.su.is_superuser = True, True

        self.u.save()
        self.st.save()
        self.pu.save()
        self.su.save()
        self.np.save()

        self.m = Manager(title="House President", url_title="president",
                         president=True)
        self.m.incumbent = UserProfile.objects.get(user=self.pu)
        self.m.save()

        self.rt = RequestType(name="Food", url_name="food", enabled=True)
        self.rt.save()
        self.rt.managers = [self.m]
        self.rt.save()

        self.a = Announcement(
            manager=self.m,
            incumbent=self.m.incumbent,
            body="Test Announcement Body",
            post_date=datetime.now(),
            )
        self.a.save()

        self.request = Request(owner=UserProfile.objects.get(user=self.u),
                               body="request body", request_type=self.rt)
        self.request.save()

        UserProfile.objects.get(user=self.np).delete()
        self.pr = ProfileRequest(username="pr", email="pr@email.com",
                     affiliation=UserProfile.STATUS_CHOICES[0][0])
        self.pr.save()

    def _admin_required(self, url, success_target=None):
        response = self.client.get(url)
        self.assertRedirects(response, "/login/?next=" + url)

        self.client.login(username="np", password="pwd")
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, "/landing/")
        self.assertContains(response, MESSAGES["NO_PROFILE"])
        self.client.logout()

        self.client.login(username="u", password="pwd")
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, "/")
        self.assertContains(response, MESSAGES["ADMINS_ONLY"])
        self.client.logout()

        self.client.login(username="st", password="pwd")
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, "/")
        self.assertContains(response, MESSAGES["ADMINS_ONLY"])
        self.client.logout()

        self.client.login(username="su", password="pwd")
        response = self.client.get(url)
        if success_target is None:
            self.assertEqual(response.status_code, 200)
        else:
            self.assertRedirects(response, success_target)
        self.client.logout()

    def _president_admin_required(self, url, success_target=None):
        response = self.client.get(url)
        self.assertRedirects(response, "/login/?next=" + url)

        self.client.login(username="np", password="pwd")
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, "/landing/")
        self.assertContains(response, MESSAGES["NO_PROFILE"])
        self.client.logout()

        self.client.login(username="u", password="pwd")
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, "/")
        self.assertContains(response, MESSAGES["PRESIDENTS_ONLY"])
        self.client.logout()

        self.client.login(username="st", password="pwd")
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, "/")
        self.assertContains(response, MESSAGES["PRESIDENTS_ONLY"])
        self.client.logout()

        self.client.login(username="su", password="pwd")
        response = self.client.get(url)
        if success_target is None:
            self.assertEqual(response.status_code, 200)
        else:
            self.assertRedirects(response, success_target)
        self.client.logout()

        self.client.login(username="pu", password="pwd")
        response = self.client.get(url)
        if success_target is None:
            self.assertEqual(response.status_code, 200)
        else:
            self.assertRedirects(response, success_target)
        self.client.logout()

    def _profile_required(self, url, success_target=None):
        response = self.client.get(url)
        self.assertRedirects(response, "/login/?next=" + url)

        self.client.login(username="np", password="pwd")
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, "/landing/")
        self.assertContains(response, MESSAGES["NO_PROFILE"])
        self.client.logout()

        self.client.login(username="u", password="pwd")
        response = self.client.get(url, follow=True)
        if success_target is None:
            self.assertEqual(response.status_code, 200)
        else:
            self.assertRedirects(response, success_target)
        self.client.logout()

        self.client.login(username="st", password="pwd")
        response = self.client.get(url, follow=True)
        if success_target is None:
            self.assertEqual(response.status_code, 200)
        else:
            self.assertRedirects(response, success_target)
        self.client.logout()

        self.client.login(username="su", password="pwd")
        response = self.client.get(url, follow=True)
        if success_target is None:
            self.assertEqual(response.status_code, 200)
        else:
            self.assertRedirects(response, success_target)
        self.client.logout()

    def test_admin_required(self):
        pages = [
            "profile_requests",
            "profile_requests/{0}".format(self.pr.pk),
            "manage_users",
            "modify_user/{0}".format(self.u.username),
            "add_user",
            "utilities",
            ]
        for page in pages:
            self._admin_required("/custom_admin/" + page + "/")
        self._admin_required("/custom_admin/recount/",
                             success_target="/custom_admin/utilities/")
        self._admin_required("/custom_admin/anonymous_login/",
                             success_target="/")
        self._admin_required("/custom_admin/end_anonymous_session/",
                             success_target="/custom_admin/utilities/")

    def test_president_admin_required(self):
        pages = [
            "managers",
            "managers/president",
            "add_manager",
            "request_types",
            "request_types/{0}".format(self.rt.url_name),
            "add_request_type",
            ]
        for page in pages:
            self._president_admin_required("/custom_admin/" + page + "/")

    def test_profile_required(self):
        pages = [
            "manager_directory",
            "manager_directory/president",
            "profile/{0}/requests".format(self.u.username),
            "requests/{0}".format(self.rt.url_name),
            "archives/all_requests",
            "requests/{0}/all".format(self.rt.url_name),
            "my_requests",
            "request/{0}".format(self.request.pk),
            "announcements",
            "announcements/{0}".format(self.a.pk),
            "announcements/{0}/edit".format(self.a.pk),
            "announcements/all",
            ]
        for page in pages:
            self._profile_required("/" + page + "/")

class TestAnonymousUser(TestCase):
    def setUp(self):
        self.u = User.objects.create_user(username="u", password="pwd")
        self.su = User.objects.create_user(username="su", password="pwd")

        self.su.is_staff, self.su.is_superuser = True, True
        self.su.save()

        self.client.login(username="su", password="pwd")

    def test_anonymous_start(self):
        response = self.client.get("/")
        self.assertNotContains(
            response,
            "Logged in as anonymous user Anonymous Coward",
            )

        response = self.client.get("/custom_admin/anonymous_login/", follow=True)
        self.assertRedirects(response, "/")
        self.assertContains(
            response,
            "Logged in as anonymous user Anonymous Coward",
            )

    def test_anonymous_end(self):
        self.client.get("/custom_admin/anonymous_login/")
        self.client.login(username="su", password="pwd")

        response = self.client.get("/custom_admin/end_anonymous_session/",
                       follow=True)
        self.assertRedirects(response, "/custom_admin/utilities/")
        self.assertContains(response, MESSAGES["ANONYMOUS_SESSION_ENDED"])
        self.assertNotContains(
            response,
            "Logged in as anonymous user Anonymous Coward",
            )

    def test_anonymous_profile(self):
        # Failing before anonymous user is first logged in
        response = self.client.get("/profile/{0}/".format(ANONYMOUS_USERNAME))
        self.assertEqual(response.status_code, 404)

        self.client.get("/custom_admin/anonymous_login/")

        response = self.client.get("/profile/{0}/".format(ANONYMOUS_USERNAME))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Anonymous Coward")

        response = self.client.get("/profile/", follow=True)
        self.assertRedirects(response, "/")
        self.assertContains(response, MESSAGES['SPINELESS'])

    def test_anonymous_edit_profile(self):
        # Failing before anonymous user is first logged in
        response = self.client.get("/custom_admin/modify_user/{0}/"
                       .format(ANONYMOUS_USERNAME))
        self.assertEqual(response.status_code, 404)

        self.client.get("/custom_admin/anonymous_login/")
        self.client.get("/logout/", follow=True)

        self.client.login(username="su", password="pwd")

        response = self.client.get("/custom_admin/modify_user/{0}/"
                       .format(ANONYMOUS_USERNAME))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Anonymous")
        self.assertContains(response, "Coward")
        self.assertContains(response, MESSAGES['ANONYMOUS_EDIT'])

    def test_anonymous_logout(self):
        self.client.get("/custom_admin/anonymous_login/")

        response = self.client.get("/logout/", follow=True)
        self.assertRedirects(response, "/")
        self.assertContains(response, MESSAGES['ANONYMOUS_DENIED'])

    def test_anonymous_user_login_logout(self):
        self.client.get("/custom_admin/anonymous_login/")

        # Need to be careful here, client.login and client.logout clear the
        # session cookies, causing this test to break
        response = self.client.post("/login/", {
                "username_or_email": "u",
                "password": "pwd",
                }, follow=True)

        self.assertRedirects(response, "/")
        self.assertNotContains(
            response,
            "Logged in as anonymous user Anonymous Coward",
            )

        response = self.client.get("/logout/", follow=True)
        self.assertRedirects(response, "/")

        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Logged in as anonymous user Anonymous Coward",
            )

class TestRequestPages(TestCase):
    def setUp(self):
        self.u = User.objects.create_user(username="u", password="pwd")
        self.pu = User.objects.create_user(username="pu", password="pwd")

        self.u.save()
        self.pu.save()

        self.m = Manager(title="House President", url_title="president",
                         president=True)
        self.m.incumbent = UserProfile.objects.get(user=self.pu)
        self.m.save()

        self.rt = RequestType(name="Food", url_name="food", enabled=True)
        self.rt.save()
        self.rt.managers = [self.m]
        self.rt.save()

        self.request = Request(owner=UserProfile.objects.get(user=self.u),
                               body="Request Body", request_type=self.rt)
        self.request.save()

        self.response = Response(owner=UserProfile.objects.get(user=self.pu),
                     body="Response Body", request=self.request,
                     manager=True)
        self.response.save()

    def test_request_form(self):
        urls = [
            "/request/{0}/".format(self.request.pk),
            "/requests/{0}/".format(self.rt.url_name),
            ]

        self.client.login(username="u", password="pwd")
        for url in urls + ["/my_requests/"]:
            response = self.client.get(url)
            self.assertContains(response, "Request Body")
            self.assertContains(response, "Response Body")
            self.assertNotContains(response, "mark_filled")
        self.client.logout()

        self.client.login(username="pu", password="pwd")
        for url in urls:
            response = self.client.get(url)
            self.assertContains(response, "Request Body")
            self.assertContains(response, "Response Body")
            self.assertContains(response, "mark_filled")

        response = self.client.get("/my_requests/")
        self.assertNotContains(response, "Request Body")
        self.assertNotContains(response, "Response Body")
        self.assertNotContains(response, "mark_filled")

class TestManager(TestCase):
    def setUp(self):
        self.su = User.objects.create_user(username="su", password="pwd")
        self.su.is_staff, self.su.is_superuser = True, True
        self.su.save()

        self.m1 = Manager(
            title="setUp Manager",
            incumbent=UserProfile.objects.get(user=self.su),
            )
        self.m1.url_title = convert_to_url(self.m1.title)
        self.m1.save()

        self.m2 = Manager(
            title="Testing Manager",
            incumbent=UserProfile.objects.get(user=self.su),
            )
        self.m2.url_title = convert_to_url(self.m2.title)
        self.m2.save()

        self.client.login(username="su", password="pwd")

    def test_add_manager(self):
        response = self.client.post("/custom_admin/add_manager/", {
                "title": "Test Manager",
                "incumbent": "1",
                "compensation": "Test % Compensation",
                "duties": "Testing Add Managers Page",
                "email": "tester@email.com",
                "president": False,
                "workshift_manager": False,
                "active": True,
                "semester_hours": 5,
                "summer_hours": 5,
                "update_manager": "",
                }, follow=True)
        self.assertRedirects(response, "/custom_admin/add_manager/")
        self.assertContains(
            response,
            MESSAGES['MANAGER_ADDED'].format(managerTitle="Test Manager"),
            )
        self.assertEqual(1, Manager.objects.filter(title="Test Manager").count())
        self.assertEqual(1, Manager.objects.filter(url_title=convert_to_url("Test Manager")).count())

    def test_duplicate_title(self):
        response = self.client.post("/custom_admin/add_manager/", {
                "title": self.m1.title,
                "incumbent": "1",
                "compensation": "Test % Compensation",
                "duties": "Testing Add Managers Page",
                "email": "tester@email.com",
                "president": False,
                "workshift_manager": False,
                "active": True,
                "update_manager": "",
                })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "A manager with this title already exists.")

    def test_duplicate_url_title(self):
        response = self.client.post("/custom_admin/add_manager/", {
                "title": "SETUP MANAGER",
                "incumbent": "1",
                "compensation": "Test % Compensation",
                "duties": "Testing Add Managers Page",
                "email": "tester@email.com",
                "president": False,
                "workshift_manager": False,
                "active": True,
                "update_manager": "",
                })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This manager title maps to a url that is already taken.  Please note, "Site Admin" and "sITe_adMIN" map to the same URL.'.replace('"', "&quot;"))

    def test_edit_manager(self):
        new_title = "New setUp Manager"
        response = self.client.post("/custom_admin/managers/{0}/"
                                    .format(self.m1.url_title), {
                "title": new_title,
                "incumbent": self.m1.incumbent.pk,
                "compensation": "Test % Compensation",
                "duties": "Testing Add Managers Page",
                "email": "tester@email.com",
                "president": False,
                "workshift_manager": False,
                "active": True,
                "semester_hours": 5,
                "summer_hours": 5,
                "update_manager": "",
                }, follow=True)
        self.assertRedirects(response, "/custom_admin/managers/")
        self.assertContains(
            response,
            MESSAGES['MANAGER_SAVED'].format(managerTitle=new_title),
            )
        self.assertEqual(1, Manager.objects.filter(title=new_title).count())
        self.assertEqual(1, Manager.objects.filter(url_title=convert_to_url(new_title)).count())

    def test_edit_title(self):
        response = self.client.post("/custom_admin/managers/{0}/"
                                    .format(self.m1.url_title), {
                "title": self.m2.title,
                "incumbent": self.m2.incumbent.pk,
                "compensation": "Test % Compensation",
                "duties": "Testing Add Managers Page",
                "email": "tester@email.com",
                "president": False,
                "workshift_manager": False,
                "active": True,
                "update_manager": "",
                }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "A manager with this title already exists.")

    def test_edit_url_title(self):
        response = self.client.post("/custom_admin/managers/{0}/"
                                    .format(self.m1.url_title), {
                "title": self.m2.url_title.upper(),
                "incumbent": self.m2.incumbent.pk,
                "compensation": "Test % Compensation",
                "duties": "Testing Add Managers Page",
                "email": "tester@email.com",
                "president": False,
                "workshift_manager": False,
                "active": True,
                "update_manager": "",
                }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This manager title maps to a url that is already taken.  Please note, "Site Admin" and "sITe_adMIN" map to the same URL.'.replace('"', "&quot;"))

class TestRequestTypes(TestCase):
    def setUp(self):
        self.su = User.objects.create_user(username="su", password="pwd")
        self.su.is_staff, self.su.is_superuser = True, True
        self.su.save()

        self.m1 = Manager(
            title="setUp Manager",
            incumbent=UserProfile.objects.get(user=self.su),
            )
        self.m1.url_title = convert_to_url(self.m1.title)
        self.m1.save()

        self.m2 = Manager(
            title="Testing Manager",
            incumbent=UserProfile.objects.get(user=self.su),
            )
        self.m2.url_title = convert_to_url(self.m2.title)
        self.m2.save()

        self.rt = RequestType(
            name="Super", url_name="super",
            )
        self.rt.save()
        self.rt.managers = [self.m1, self.m2]
        self.rt.save()

        self.rt2 = RequestType(
            name="Duper", url_name="duper",
            )
        self.rt2.save()

        self.client.login(username="su", password="pwd")

    def test_manage_view(self):
        response = self.client.get("/custom_admin/request_types/")
        self.assertContains(response, self.rt.name)
        self.assertContains(response, self.rt.url_name)
        self.assertContains(response, self.m1.title)
        self.assertContains(response, self.m1.url_title)
        self.assertContains(response, self.m2.title)
        self.assertContains(response, self.m2.url_title)

    def test_add_request(self):
        name = "Cleanliness"
        response = self.client.post("/custom_admin/add_request_type/", {
            "name": name,
            "managers": [self.m1.pk, self.m2.pk],
            }, follow=True)
        self.assertRedirects(response, "/custom_admin/request_types/")
        self.assertContains(response,
                            MESSAGES['REQUEST_TYPE_ADDED'].format(typeName=name))
        rt = RequestType.objects.get(name=name)
        self.assertIn(self.m1, rt.managers.all())
        self.assertIn(self.m2, rt.managers.all())

    def test_edit_request(self):
        response = self.client.post(
            "/custom_admin/request_types/{0}/".format(self.rt.url_name), {
                "name": "New Name",
                "managers": [self.m2.pk],
                "enabled": False,
                })
        self.assertRedirects(response, "/custom_admin/request_types/")
        rt = RequestType.objects.get(pk=self.rt.pk)
        self.assertNotIn(self.m1, rt.managers.all())
        self.assertIn(self.m2, rt.managers.all())
        self.assertEqual(rt.enabled, False)
        self.assertEqual(rt.name, "New Name")
        self.assertEqual(rt.url_name, "new_name")

    def test_add_duplicate_name(self):
        response = self.client.post("/custom_admin/add_request_type/", {
            "name": self.rt.name,
            })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "A request type with this name already exists.")

    def test_edit_duplicate_name(self):
        response = self.client.post(
            "/custom_admin/request_types/{0}/".format(self.rt2.url_name), {
            "name": self.rt.name,
            })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "A request type with this name already exists.")

    def test_add_duplicate_url_name(self):
        response = self.client.post("/custom_admin/add_request_type/", {
            "name": self.rt.name.upper(),
            })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This request type name maps to a url that is already taken.  Please note, "Waste Reduction" and "wasTE_RedUCtiON" map to the same URL.'.replace('"', "&quot;"))

    def test_edit_duplicate_url_name(self):
        response = self.client.post(
            "/custom_admin/request_types/{0}/".format(self.rt2.url_name), {
            "name": self.rt.name.upper(),
            })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This request type name maps to a url that is already taken.  Please note, "Waste Reduction" and "wasTE_RedUCtiON" map to the same URL.'.replace('"', "&quot;"))

class TestAnnouncements(TestCase):
    def setUp(self):
        self.u = User.objects.create_user(username="u", password="pwd")
        self.ou = User.objects.create_user(username="ou", password="pwd")
        self.su = User.objects.create_user(username="su", password="pwd")

        self.su.is_staff, self.su.is_superuser = True, True
        self.su.save()

        self.m = Manager(
            title="setUp Manager",
            incumbent=UserProfile.objects.get(user=self.u),
            )
        self.m.url_title = convert_to_url(self.m.title)
        self.m.save()

        self.a = Announcement(
            manager=self.m,
            incumbent=self.m.incumbent,
            body="Test Announcement Body",
            post_date=datetime.now(),
            )
        self.a.save()

        self.client.login(username="u", password="pwd")

    def test_announcements(self):
        response = self.client.get("/announcements/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.a.body)

    def test_individual(self):
        response = self.client.get("/announcements/{0}/".format(self.a.pk))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.a.body)

    def test_edit_announcement(self):
        url = "/announcements/{0}/edit/".format(self.a.pk)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.a.body)

        new_body = "New Test Announcement Body"
        response = self.client.post("/announcements/{0}/edit/".format(self.a.pk), {
                "body": new_body,
                "manager": self.a.manager.pk,
                }, follow=True)

        self.assertRedirects(response, "/announcements/{0}/".format(self.a.pk))
        self.assertContains(response, new_body)

        self.assertEqual(new_body, Announcement.objects.get(pk=self.a.pk).body)

    @override_settings(ANNOUNCEMENT_LIFE=0)
    def test_unpin(self):
        self.a.pinned = True
        self.a.save()
        response = self.client.post("/announcements/", {
                "announcement_pk": self.a.pk,
                "unpin": "",
                }, follow=True)
        self.assertRedirects(response, "/announcements/")
        self.assertNotContains(response, self.a.body)

    def test_no_edit(self):
        self.client.logout()
        self.client.login(username="ou", password="pwd")

        response = self.client.get("/announcements/{0}/edit/".format(self.a.pk))
        self.assertRedirects(response, "/announcements/{0}/".format(self.a.pk))

        self.client.logout()
        self.client.login(username="su", password="pwd")

        response = self.client.get("/announcements/{0}/edit/".format(self.a.pk))
        self.assertEqual(response.status_code, 200)

    @override_settings(ANNOUNCEMENT_LIFE=0)
    def test_unpin_individual(self):
        self.a.pinned = True
        self.a.save()
        url = "/announcements/{0}/".format(self.a.pk)
        response = self.client.post(url, {
                "unpin": "",
                }, follow=True)
        self.assertRedirects(response, url)
        self.assertContains(response, self.a.body)

        response = self.client.get("/announcements/")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.a.body)

class TestPreFill(TestCase):
    def test_pre_fill(self):
        from farnsworth.pre_fill import main, REQUESTS, MANAGERS
        main([])
        for title in [i[0] for i in MANAGERS]:
            self.assertEqual(1, Manager.objects.filter(title=title).count())
        for name in [i[0] for i in REQUESTS]:
            self.assertEqual(1, RequestType.objects.filter(name=name).count())

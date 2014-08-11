
from django.core.urlresolvers import reverse
from django.test import TestCase

from base.models import User, UserProfile
from rooms.models import Room

class TestViews(TestCase):
    def setUp(self):
        self.su = User.objects.create_user(username="su", password="pwd")

        self.su.is_staff, self.su.is_superuser = True, True
        self.su.first_name = "Super"
        self.su.last_name = "User"
        self.su.save()

        self.r = Room.objects.create(title="2E")
        self.r.current_residents = [UserProfile.objects.get(user=self.su)]
        self.r.save()

        self.client.login(username="su", password="pwd")

    def test_list(self):
        url = reverse("rooms:list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.r.title)
        self.assertNotContains(response, "Login")
        self.assertContains(response, self.su.get_full_name())

    def test_add(self):
        url = reverse("rooms:add")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Login")

    def test_view(self):
        url = reverse("rooms:view", kwargs={"room_title": self.r.title})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.r.title)
        self.assertContains(response, self.su.get_full_name())
        self.assertNotContains(response, "Login")

    def test_edit(self):
        url = reverse("rooms:edit", kwargs={"room_title": self.r.title})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.r.title)
        self.assertNotContains(response, "Login")

class TestAddRoom(TestCase):
    def setUp(self):
        self.su = User.objects.create_user(username="su", password="pwd")

        self.su.is_staff, self.su.is_superuser = True, True
        self.su.first_name = "Super"
        self.su.last_name = "User"
        self.su.save()

        self.client.login(username="su", password="pwd")

    def test_add_room(self):
        url = reverse("rooms:add")
        response = self.client.post(url, {
            "title": "2E",
            "unofficial_name": "Starry Night",
            "description": "Home to the best person on earth.",
            "occupancy": 1,
            "add_room": "",
        }, follow=True)
        self.assertRedirects(response, reverse("rooms:list"))
        self.assertContains(response, "2E")
        self.assertContains(response, "<td>1</td>")
        self.assertContains(response, "Starry Night")
        self.assertNotContains(
            response,
            "Home to the best person on earth.",
            )
        self.assertNotContains(response, self.su.get_full_name())

    def test_no_duplicate(self):
        r = Room(title="1A")
        r.save()

        url = reverse("rooms:add")
        response = self.client.post(url, {
            "title": r.title,
            "unofficial_name": "",
            "description": "",
            "occupancy": 1,
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Room with this Title already exists.",
            )

    def test_bad_title(self):
        url = reverse("rooms:add")
        response = self.client.post(url, {
            "title": "",
            "unofficial_name": "",
            "description": "",
            "occupancy": 1,
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "This field is required.",
            )

        response = self.client.post(url, {
            "title": "2e.",
            "unofficial_name": "",
            "description": "",
            "occupancy": 1,
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Only alphanumeric characters are allowed.",
            )

        response = self.client.post(url, {
            "title": "2_",
            "unofficial_name": "",
            "description": "",
            "occupancy": 1,
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Only alphanumeric characters are allowed.",
            )

    def test_bad_occupancy(self):
        url = reverse("rooms:add")
        response = self.client.post(url, {
            "title": "2E",
            "unofficial_name": "Starry Night",
            "description": "Home to the best person on earth.",
            "occupancy": -1,
            })
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Ensure this value is greater than or equal to 0.",
            )

        response = self.client.post(url, {
            "title": "2E",
            "unofficial_name": "Starry Night",
            "description": "Home to the best person on earth.",
            "occupancy": "",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "This field is required.",
            )

    def test_add_room_minimal(self):
        url = reverse("rooms:add")
        response = self.client.post(url, {
            "title": "2E",
            "unofficial_name": "",
            "description": "",
            "occupancy": 1,
        }, follow=True)
        self.assertRedirects(response, reverse("rooms:list"))
        self.assertContains(response, "2E")
        self.assertContains(response, "<td>1</td>")
        self.assertNotContains(response, "Starry Night")
        self.assertNotContains(
            response,
            "Home to the best person on earth.",
            )
        self.assertNotContains(response, self.su.get_full_name())

class TestEditRoom(TestCase):
    def setUp(self):
        self.su = User.objects.create_user(username="su", password="pwd")

        self.su.is_staff, self.su.is_superuser = True, True
        self.su.first_name = "Super"
        self.su.last_name = "User"
        self.su.save()

        self.r = Room(title="2E")
        self.r.save()

        self.client.login(username="su", password="pwd")

    def test_edit_room(self):
        url = reverse("rooms:edit", kwargs={"room_title": self.r.title})
        response = self.client.post(url, {
            "room-title": self.r.title,
            "room-unofficial_name": "Starry Night Surprise",
            "room-description": "Previous home to the best person on earth.",
            "room-occupancy": 5,
            "residents-TOTAL_FORMS": 0,
            "residents-INITIAL_FORMS": 0,
            "residents-MAX_NUM_FORMS": 50,
            }, follow=True)

        url = reverse("rooms:view", kwargs={"room_title": self.r.title})
        self.assertRedirects(response, url)
        self.assertContains(response, "2E")
        self.assertContains(response, "<dd>{0}</dd>".format(5), html=True)
        self.assertContains(response, "Starry Night Surprise")
        self.assertContains(
            response,
            "Previous home to the best person on earth.",
            )
        self.assertNotContains(response, self.su.get_full_name())

    def test_no_duplicate(self):
        r = Room.objects.create(title="1A")

        url = reverse("rooms:edit", kwargs={"room_title": self.r.title})
        response = self.client.post(url, {
            "room-title": r.title,
            "room-unofficial_name": "",
            "room-description": "",
            "room-occupancy": 1,
            "residents-TOTAL_FORMS": 0,
            "residents-INITIAL_FORMS": 0,
            "residents-MAX_NUM_FORMS": 50,
            })

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Room with this Title already exists.",
            )

    def test_edit_room_minimal(self):
        url = reverse("rooms:edit", kwargs={"room_title": self.r.title})
        response = self.client.post(url, {
            "room-title": self.r.title,
            "room-unofficial_name": "",
            "room-description": "",
            "room-occupancy": 5,
            "residents-TOTAL_FORMS": 0,
            "residents-INITIAL_FORMS": 0,
            "residents-MAX_NUM_FORMS": 50,
            }, follow=True)

        url = reverse("rooms:view", kwargs={"room_title": self.r.title})
        self.assertRedirects(response, url)
        self.assertContains(response, "<dd>{0}</dd>".format(5), html=True)
        self.assertNotContains(response, "Starry Night Surprise")
        self.assertNotContains(response, self.su.get_full_name())

    def test_bad_occupancy(self):
        url = reverse("rooms:edit", kwargs={"room_title": self.r.title})
        response = self.client.post(url, {
            "room-title": self.r.title,
            "room-unofficial_name": "Starry Night",
            "room-description": "Home to the best person on earth.",
            "room-occupancy": -1,
            "residents-TOTAL_FORMS": 0,
            "residents-INITIAL_FORMS": 0,
            "residents-MAX_NUM_FORMS": 50,
            })

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Ensure this value is greater than or equal to 0.",
            )

        response = self.client.post(url, {
            "title": self.r.title,
            "unofficial_name": "Starry Night",
            "description": "Home to the best person on earth.",
            "occupancy": "",
            "residents-TOTAL_FORMS": 0,
            "residents-INITIAL_FORMS": 0,
            "residents-MAX_NUM_FORMS": 50,
            })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required.")

    def test_bad_title(self):
        url = reverse("rooms:edit", kwargs={"room_title": self.r.title})
        response = self.client.post(url, {
            "room-title": "",
            "room-unofficial_name": "",
            "room-description": "",
            "room-occupancy": 1,
            "residents-TOTAL_FORMS": 0,
            "residents-INITIAL_FORMS": 0,
            "residents-MAX_NUM_FORMS": 50,
            })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required.")

        response = self.client.post(url, {
            "room-title": "2a.",
            "room-unofficial_name": "",
            "room-description": "",
            "room-occupancy": 1,
            "residents-TOTAL_FORMS": 0,
            "residents-INITIAL_FORMS": 0,
            "residents-MAX_NUM_FORMS": 50,
            })

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Only alphanumeric characters are allowed.",
            )

        response = self.client.post(url, {
            "room-title": "3_",
            "room-unofficial_name": "",
            "room-description": "",
            "room-occupancy": 1,
            "residents-TOTAL_FORMS": 0,
            "residents-INITIAL_FORMS": 0,
            "residents-MAX_NUM_FORMS": 50,
            })

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Only alphanumeric characters are allowed.",
            )

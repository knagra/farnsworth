from django.test import TestCase

from base.models import User, UserProfile
from rooms.models import Room

class TestViews(TestCase):
	def setUp(self):
		self.r = Room(title="2E")
		self.r.save()

		self.su = User.objects.create_user(username="su", password="pwd")

		self.su.is_staff, self.su.is_superuser = True, True
		self.su.first_name = "Super"
		self.su.last_name = "User"
		self.su.save()

		profile = UserProfile.objects.get(user=self.su)
		profile.current_room = self.r
		profile.save()

		self.client.login(username="su", password="pwd")

	def test_list(self):
		response = self.client.get("/rooms/")
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, self.r.title)
		self.assertNotContains(response, "Login")
		self.assertContains(response,
                            "{0} {1}".format(self.su.first_name, self.su.last_name))

	def test_add(self):
		response = self.client.get("/rooms/add")
		self.assertEqual(response.status_code, 200)
		self.assertNotContains(response, "Login")

	def test_view(self):
		response = self.client.get("/room/{0}/".format(self.r.title))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, self.r.title)
		self.assertContains(
            response,
            "{0} {1}".format(self.su.first_name, self.su.last_name),
            )
		self.assertNotContains(response, "Login")

	def test_edit(self):
		response = self.client.get("/room/{0}/edit".format(self.r.title))
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
		response = self.client.post("/rooms/add", {
			"title": "2E",
			"unofficial_name": "Starry Night",
			"description": "Home to the best person on earth.",
			"occupancy": 1,
			"add_room": "",
		}, follow=True)
		self.assertRedirects(response, "/rooms/")
		self.assertContains(response, "2E")
		self.assertContains(response, "<td>1</td>")
		self.assertContains(response, "Starry Night")
		self.assertNotContains(
            response,
            "Home to the best person on earth.",
            )
		self.assertNotContains(
            response,
            "{0} {1}".format(self.su.first_name, self.su.last_name),
            )

	def test_no_duplicate(self):
		r = Room(title="1A")
		r.save()

		response = self.client.post("/rooms/add", {
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
		response = self.client.post("/rooms/add", {
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

		response = self.client.post("/rooms/add", {
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

		response = self.client.post("/rooms/add", {
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
		response = self.client.post("/rooms/add", {
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

		response = self.client.post("/rooms/add", {
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
		response = self.client.post("/rooms/add", {
			"title": "2E",
			"unofficial_name": "",
			"description": "",
			"occupancy": 1,
		}, follow=True)
		self.assertRedirects(response, "/rooms/")
		self.assertContains(response, "2E")
		self.assertContains(response, "<td>1</td>")
		self.assertNotContains(response, "Starry Night")
		self.assertNotContains(
            response,
            "Home to the best person on earth.",
            )
		self.assertNotContains(
            response,
            "{0} {1}".format(self.su.first_name, self.su.last_name),
            )

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
		response = self.client.post("/room/{0}/edit".format(self.r.title), {
			"title": self.r.title,
			"unofficial_name": "Starry Night Surprise",
			"description": "Previous home to the best person on earth.",
			"occupancy": 5,
		}, follow=True)
		self.assertRedirects(response, "/room/{0}/".format(self.r.title))
		self.assertContains(response, "2E")
		self.assertContains(response, "Total occupancy: 5")
		self.assertContains(response, "Starry Night Surprise")
		self.assertContains(
            response,
            "Previous home to the best person on earth.",
            )
		self.assertNotContains(
            response,
            "{0} {1}".format(self.su.first_name, self.su.last_name),
            )

	def test_no_duplicate(self):
		r = Room(title="1A")
		r.save()

		response = self.client.post("/room/{0}/edit".format(self.r.title), {
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

	def test_edit_room_minimal(self):
		response = self.client.post("/room/{0}/edit".format(self.r.title), {
			"title": self.r.title,
			"unofficial_name": "",
			"description": "",
			"occupancy": 5,
		}, follow=True)
		self.assertRedirects(response, "/room/{0}/".format(self.r.title))
		self.assertContains(response, "Total occupancy: 5")
		self.assertNotContains(response, "Starry Night Surprise")
		self.assertNotContains(
            response,
            "{0} {1}".format(self.su.first_name, self.su.last_name),
			)

	def test_bad_occupancy(self):
		response = self.client.post("/room/{0}/edit".format(self.r.title), {
			"title": self.r.title,
			"unofficial_name": "Starry Night",
			"description": "Home to the best person on earth.",
			"occupancy": -1,
		})
		self.assertEqual(response.status_code, 200)
		self.assertContains(
            response,
            "Ensure this value is greater than or equal to 0.",
            )

		response = self.client.post("/room/{0}/edit".format(self.r.title), {
			"title": self.r.title,
			"unofficial_name": "Starry Night",
			"description": "Home to the best person on earth.",
			"occupancy": "",
		})
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "This field is required.")

	def test_bad_title(self):
		response = self.client.post("/room/{0}/edit".format(self.r.title), {
			"title": "",
			"unofficial_name": "",
			"description": "",
			"occupancy": 1,
		})
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "This field is required.")

		response = self.client.post("/room/{0}/edit".format(self.r.title), {
			"title": "2a.",
			"unofficial_name": "",
			"description": "",
			"occupancy": 1,
		})
		self.assertEqual(response.status_code, 200)
		self.assertContains(
            response,
            "Only alphanumeric characters are allowed.",
            )

		response = self.client.post("/room/{0}/edit".format(self.r.title), {
			"title": "3_",
			"unofficial_name": "",
			"description": "",
			"occupancy": 1,
		})
		self.assertEqual(response.status_code, 200)
		self.assertContains(
            response,
            "Only alphanumeric characters are allowed.",
            )

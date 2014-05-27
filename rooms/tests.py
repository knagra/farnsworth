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

		self.r = Room(title="2E")
		self.r.save()
		self.r.residents = UserProfile.objects.filter(user=self.su)

		self.client.login(username="su", password="pwd")

	def test_list(self):
		response = self.client.get("/rooms/")
		self.assertEqual(response.status_code, 200)
		self.assertIn(self.r.title, response.content)
		self.assertNotIn("Login", response.content)

	def test_add(self):
		response = self.client.get("/rooms/add")
		self.assertEqual(response.status_code, 200)
		self.assertNotIn("Login", response.content)

	def test_view(self):
		response = self.client.get("/room/{0}/".format(self.r.title))
		self.assertEqual(response.status_code, 200)
		self.assertIn(self.r.title, response.content)
		self.assertIn("{0} {1}".format(self.su.first_name, self.su.last_name),
					  response.content)
		self.assertNotIn("Login", response.content)

	def test_edit(self):
		response = self.client.get("/room/{0}/edit".format(self.r.title))
		self.assertEqual(response.status_code, 200)
		self.assertIn(self.r.title, response.content)
		self.assertNotIn("Login", response.content)

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
		self.assertIn("2E", response.content)
		self.assertIn("<td>1</td>", response.content)
		self.assertIn("Starry Night", response.content)
		self.assertNotIn("Home to the best person on earth.", response.content)
		self.assertNotIn("{0} {1}".format(self.su.first_name, self.su.last_name),
						response.content)

	def test_bad_occupancy(self):
		response = self.client.post("/rooms/add", {
			"title": "2E",
			"unofficial_name": "Starry Night",
			"description": "Home to the best person on earth.",
			"occupancy": -1,
		})
		self.assertEqual(response.status_code, 200)
		self.assertIn("Ensure this value is greater than or equal to 0.", response.content)

		response = self.client.post("/rooms/add", {
			"title": "2E",
			"unofficial_name": "Starry Night",
			"description": "Home to the best person on earth.",
			"occupancy": "",
		})
		self.assertEqual(response.status_code, 200)
		self.assertIn("This field is required.", response.content)

	def test_add_room_minimal(self):
		response = self.client.post("/rooms/add", {
			"title": "2E",
			"unofficial_name": "",
			"description": "",
			"occupancy": 1,
		}, follow=True)
		self.assertRedirects(response, "/rooms/")
		self.assertIn("2E", response.content)
		self.assertIn("<td>1</td>", response.content)
		self.assertNotIn("Starry Night", response.content)
		self.assertNotIn("Home to the best person on earth.", response.content)
		self.assertNotIn("{0} {1}".format(self.su.first_name, self.su.last_name),
						response.content)

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
			"unofficial_name": "Starry Night Surprise",
			"description": "Previous home to the best person on earth.",
			"occupancy": 5,
			"residents": self.su.pk,
		}, follow=True)
		self.assertRedirects(response, "/room/{0}/".format(self.r.title))
		self.assertIn("2E", response.content)
		self.assertIn("Total occupancy: 5", response.content)
		self.assertIn("Starry Night Surprise", response.content)
		self.assertIn("Previous home to the best person on earth.", response.content)
		self.assertIn("{0} {1}".format(self.su.first_name, self.su.last_name),
					  response.content)

	def test_edit_room_minimal(self):
		response = self.client.post("/room/{0}/edit".format(self.r.title), {
			"unofficial_name": "",
			"description": "",
			"occupancy": 5,
			"residents": self.su.pk,
		}, follow=True)
		self.assertRedirects(response, "/room/{0}/".format(self.r.title))
		self.assertIn("Total occupancy: 5", response.content)
		self.assertNotIn("Starry Night Surprise", response.content)
		self.assertIn("{0} {1}".format(self.su.first_name, self.su.last_name),
					  response.content)

	def test_bad_occupancy(self):
		response = self.client.post("/room/{0}/edit".format(self.r.title), {
			"unofficial_name": "Starry Night",
			"description": "Home to the best person on earth.",
			"occupancy": -1,
		})
		self.assertEqual(response.status_code, 200)
		self.assertIn("Ensure this value is greater than or equal to 0.", response.content)

		response = self.client.post("/room/{0}/edit".format(self.r.title), {
			"unofficial_name": "Starry Night",
			"description": "Home to the best person on earth.",
			"occupancy": "",
		})
		self.assertEqual(response.status_code, 200)
		self.assertIn("This field is required.", response.content)

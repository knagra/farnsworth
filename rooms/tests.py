from django.test import TestCase

from base.models import User, UserProfile
from rooms.models import Room

class TestViews(TestCase):
	def setUp(self):
		self.su = User.objects.create_user(username="su", password="pwd")
		self.su.is_staff, self.su.is_superuser = True, True
		self.su.save()

		self.r = Room(title="2E")
		self.r.save()
		self.r.residents = UserProfile.objects.filter(user=self.su)

		self.client.login(username="su", password="pwd")

	def test_list(self):
		response = self.client.get("/rooms/")
		self.assertEqual(response.status_code, 200)

	def test_add(self):
		response = self.client.get("/rooms/add")
		self.assertEqual(response.status_code, 200)

	def test_view(self):
		response = self.client.get("/room/{0}/".format(self.r.title))
		self.assertEqual(response.status_code, 200)

	def test_edit(self):
		response = self.client.get("/room/{0}/edit".format(self.r.title))
		self.assertEqual(response.status_code, 200)

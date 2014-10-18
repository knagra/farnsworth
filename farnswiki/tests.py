"""
Project: Farnsworth

Authors: Karandeep Singh Nagra and Nader Morshed

XXX:
This module is deprecated and marked for replacement.
"""

from datetime import datetime

from django.test import TestCase
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from wiki.models import Wiki, Page, Revision, MediaFile


class TestListPage(TestCase):
    """ Test list page. """

    def setUp(self):
        self.u = User.objects.create_user(username="u", first_name="John",
                                          last_name="Smith", password="pwd")
        self.su = User.objects.create_user(username="su", password="pwd")
        self.su.superuser = True
        self.su.save()

        self.addr = reverse('wiki_all')

    def test_page(self):
        response = self.client.get(self.addr, follow=True)
        self.assertRedirects(response, reverse('login') + "?next=" + self.addr)

        self.client.login(username="u", password="pwd")
        response = self.client.get(self.addr, follow=True)
        self.assertEqual(response.status_code, 200)
        for x in ('All Pages', 'Page Name', 'No wiki pages have been added yet'):
            self.assertContains(response, x)

        page = Page(slug="page")
        page.save()
        revision = Revision(page=page, content="page", content_html="",
                            created_ip="0.0.0.0", created_at=datetime.now(),
                            created_by=self.u)
        revision.save()

        response = self.client.get(self.addr, follow=True)
        self.assertEqual(response.status_code, 200)
        for x in ('Page', 'Last Edited', 'page'):
            self.assertContains(response, x)


class TestAddPage(TestCase):
    """ Test the add page. """

    def setUp(self):
        self.u = User.objects.create_user(username="u", first_name="A",
                                          last_name="B", password="pwd")
        self.su = User.objects.create_user(username="su", first_name="C",
                                           last_name="D", password="pwd")
        self.su.superuser = True
        self.su.save()

        self.addr = reverse('wiki_add')
        self.full_addr = self.addr + "?slug=page"

    def test_page(self):
        response = self.client.get(self.full_addr, follow=True)
        self.assertRedirects(response, reverse('login') + "?next=" + self.addr)

        self.client.login(username="u", password="pwd")
        response = self.client.get(self.full_addr, follow=True)
        for x in ('Add page', 'Back', 'Message', 'Save'):
            self.assertContains(response, x)

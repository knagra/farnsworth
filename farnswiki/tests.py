"""
Project: Farnsworth

Authors: Karandeep Singh Nagra and Nader Morshed

XXX:
This module is deprecated and marked for replacement.
"""

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils.timezone import now
from django.test import TestCase

from wiki.models import Wiki, Page, Revision, MediaFile


class TestListPage(TestCase):
    """ Test list page. """

    def setUp(self):
        self.u = User.objects.create_user(username="u", password="pwd")
        self.su = User.objects.create_user(username="su", password="pwd")
        self.su.is_superuser = True
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

        page = Page.objects.create(slug="page")
        Revision.objects.create(
            page=page, content="page", content_html="",
            created_ip="0.0.0.0", created_at=now(),
            created_by=self.u,
        )

        response = self.client.get(self.addr, follow=True)
        self.assertEqual(response.status_code, 200)
        for x in ('Page', 'Last Edited', 'page'):
            self.assertContains(response, x)

class TestAddPage(TestCase):
    """ Test the add page. """

    def setUp(self):
        self.u = User.objects.create_user(username="u", password="pwd")
        self.su = User.objects.create_user(username="su", password="pwd")
        self.su.is_superuser = True
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

class TestLanding(TestCase):

    def setUp(self):
        self.u = User.objects.create_user(username="u", password="pwd")
        self.su = User.objects.create_user(username="su", password="pwd")
        self.su.is_superuser = True
        self.su.save()

    def test_no_landing(self):
        response = self.client.get(reverse("external"))
        self.assertContains(
            response,
            'We are a member house of the <a href="//bsc.coop">Berkeley Student Co',
            )

    def test_add_landing(self):
        url = reverse("wiki_add") + "?slug=landing"

        self.client.login(username="u", password="pwd")
        response = self.client.get(url, follow=True)
        self.assertRedirects(
            response,
            reverse("wiki_all"),
            )
        self.assertContains(response, "You do not have permission to create this page.")

        self.client.logout()
        self.client.login(username="su", password="pwd")

        content = "New homepage content"
        message = "Created homepage"

        response = self.client.post(url, {
            "edit": "",
            "content": content,
            "message": message,
            }, follow=True)
        self.assertRedirects(
            response,
            reverse(settings.WIKI_BINDERS[0].page_url_name, kwargs={"slug": "landing"}),
            )

        self.assertEqual(
            Revision.objects.filter(content=content, message=message,
                                    page__slug="landing").count(),
            1,
            )

        response = self.client.get(reverse("external"))
        self.assertContains(
            response,
            content,
            )

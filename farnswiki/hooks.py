"""
XXX:
This module is deprecated and marked for replacement.
"""
from wiki.hooks import WikiDefaultHookset

from managers.models import Manager

from utils.variables import ANONYMOUS_USERNAME

class ProjectWikiHookset(WikiDefaultHookset):
    def _perm_check(self, wiki, user):
        return user.is_authenticated() and \
          user.is_active and \
          user.username != ANONYMOUS_USERNAME

    def _manager_check(self, user):
        return Manager.objects.filter(incumbent__user=user).count() > 0 or \
          user.is_staff or \
          user.is_superuser

    def _check_landing(self, slug, user):
        return slug != "landing" or \
          self._manager_check(user)

    def can_create_page(self, wiki, user, slug=None):
        return self._perm_check(wiki, user) and \
          self._check_landing(slug, user)

    def can_edit_page(self, page, user):
        return self._perm_check(page.wiki, user) and \
          self._check_landing(page.slug, user)

    def can_delete_page(self, page, user):
        return self._perm_check(page.wiki, user) and \
          self._manager_check(user)

    def can_view_page(self, page, user):
        return True

def parse(wiki, content):
    return content

"""
XXX:
This module is deprecated and marked for replacement.
"""


from django.conf.urls import url, patterns

from django.conf import settings

urlpatterns = patterns(
    "farnswiki.views",
)

for binder in settings.WIKI_BINDERS:
    urlpatterns += patterns(
        "farnswiki.views",
        url(binder.root + r"/page/(?P<slug>[^/]+)/$", "page", {"binder": binder}, name=binder.page_url_name),
        url(binder.root + r"/page/(?P<slug>[^/]+)/edit/$", "edit", {"binder": binder}, name=binder.edit_url_name),
    )
    urlpatterns += patterns(
        "farnswiki.views",
        url(binder.root + r"/$", "all_pages_view", {"binder": binder}, name="wiki_all"),
        url(binder.root + r"/add/$", "add_page_view", {"binder": binder}, name="wiki_add"),
        url(binder.root + r"/page/(?P<slug>[^/]+)/history/$", "history_view", {"binder": binder}, name="wiki_history"),
    )

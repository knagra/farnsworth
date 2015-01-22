"""
XXX:
This module is deprecated and marked for replacement.
"""


from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render_to_response
from django.template import RequestContext

from wiki.forms import RevisionForm
from wiki.hooks import hookset
from wiki.models import Page, Revision

from base.decorators import profile_required

def add_wiki_context(request):
    return {
        "WIKI_ENABLED": True,
        }

def add_archive_context(request):
    return {
        }

@profile_required
def page(request, slug, binder, *args, **kwargs):
    wiki = binder.lookup(*args, **kwargs)
    try:
        if wiki:
            page = wiki.pages.get(slug=slug)
        else:
            page = Page.objects.get(slug=slug)
        if not hookset.can_view_page(page, request.user):
            raise Http404()

        try:
            rev = page.revisions.get(pk=request.GET.get("rev", "-1"))
        except Revision.DoesNotExist:
            rev = page.revisions.latest()
    except Page.DoesNotExist:
        return HttpResponseRedirect(binder.edit_url(wiki, slug))

    return render_to_response("wiki/page.html", {
        "revision": rev,
        "can_edit": hookset.can_edit_page(page, request.user),
    }, context_instance=RequestContext(request))

@profile_required
def edit(request, slug, binder, *args, **kwargs):
    wiki = binder.lookup(*args, **kwargs)
    try:
        if wiki:
            page = wiki.pages.get(slug=slug)
        else:
            page = Page.objects.get(slug=slug)
    except Page.DoesNotExist:
        return HttpResponseRedirect(reverse("wiki_add") + "?slug=" + slug)
    else:
        if not hookset.can_edit_page(page, request.user):
            messages.add_message(request, messages.ERROR,
                                 "You do not have permission to edit this page.")
            return HttpResponseRedirect(reverse("wiki_all"))
        rev = page.revisions.latest()

    form = RevisionForm(
        request.POST if "edit" in request.POST else None,
        revision=rev,
    )
    if form.is_valid():
        revision = form.save(commit=False)
        revision.page = page
        revision.created_by = request.user
        revision.created_ip = request.META.get(settings.WIKI_IP_ADDRESS_META_FIELD,
                                               request.META.get("REMOTE_ADDR"))
        revision.parse()
        revision.save()
        return HttpResponseRedirect(binder.page_url(wiki, slug))

    form.fields["content"].help_text = ""

    can_delete = hookset.can_delete_page(page, request.user) and page.pk

    if can_delete and "delete" in request.POST:
        page.delete()
        return HttpResponseRedirect(reverse("wiki_all"))

    page_name = "Edit {0}".format(page.slug)

    return render_to_response("wiki/edit.html", {
        "page_name": page_name,
        "form": form,
        "page": page,
        "can_delete": can_delete,
    }, context_instance=RequestContext(request))

@profile_required
def add_page_view(request, binder, *args, **kwargs):
    wiki = binder.lookup(*args, **kwargs)
    slug = request.GET.get("slug", "")
    if not slug:
        slug = "Page Name"

    try:
        if wiki:
            page = wiki.pages.get(slug=slug)
        else:
            page = Page.objects.get(slug=slug)
    except Page.DoesNotExist:
        pass
    else:
        return HttpResponseRedirect(page.get_edit_url())

    if not hookset.can_create_page(wiki, request.user, slug=slug):
        messages.add_message(request, messages.ERROR,
                             "You do not have permission to create this page.")
        return HttpResponseRedirect(reverse("wiki_all"))

    form = RevisionForm(
        request.POST if "edit" in request.POST else None,
        revision=None,
    )
    if form.is_valid():
        page = Page.objects.create(wiki=wiki, slug=slug)
        revision = form.save(commit=False)
        revision.page = page
        revision.created_by = request.user
        revision.created_ip = request.META.get(settings.WIKI_IP_ADDRESS_META_FIELD,
                                               request.META.get("REMOTE_ADDR"))
        revision.parse()
        revision.save()
        return HttpResponseRedirect(binder.page_url(wiki, slug))

    form.fields["content"].help_text = ""

    page_name = "Add {0}".format(slug)

    return render_to_response("wiki/edit.html", {
        "page_name": page_name,
        "form": form,
        "can_delete": False,
    }, context_instance=RequestContext(request))

@profile_required
def history_view(request, slug, binder, *args, **kwargs):
    wiki = binder.lookup(*args, **kwargs)
    try:
        if wiki:
            page = wiki.pages.get(slug=slug)
        else:
            page = Page.objects.get(slug=slug)
        rev = page.revisions.latest()
        if not hookset.can_view_page(page, request.user):
            raise Http404()
    except Page.DoesNotExist:
        raise Http404()

    page_name = "History for {0}".format(page.slug)
    return render_to_response("wiki/history.html", {
        "page_name": page_name,
        "page": page,
    }, context_instance=RequestContext(request))

@profile_required
def all_pages_view(request, binder, *args, **kwargs):
    wiki = binder.lookup(*args, **kwargs)
    if wiki:
        pages = wiki.pages.all()
    else:
        pages = Page.objects.all()

    pages = [
        page
        for page in pages
        if hookset.can_view_page(page, request.user)
    ]

    page_name = "All Pages"
    can_add = hookset.can_create_page(wiki, request.user)
    return render_to_response("wiki/all.html", {
        "page_name": page_name,
        "pages": pages,
        "can_add": can_add,
    }, context_instance=RequestContext(request))

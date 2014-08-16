
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404, HttpResponseForbidden
from django.shortcuts import render_to_response, render, get_object_or_404
from django.template import RequestContext
from django.views import static
from django.views.decorators.http import require_POST

from wiki.forms import RevisionForm
from wiki.hooks import hookset
from wiki.models import Page, Revision, MediaFile

from base.decorators import profile_required

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
        rev = page.revisions.latest()
        if not hookset.can_edit_page(page, request.user):
            return HttpResponseForbidden()
    except Page.DoesNotExist:
        page = Page(wiki=wiki, slug=slug)
        rev = None
        if not hookset.can_edit_page(page, request.user):
            raise Http404()
    if request.method == "POST":
        form = RevisionForm(request.POST, revision=rev)
        if form.is_valid():
            if page.pk is None:
                page.save()
            revision = form.save(commit=False)
            revision.page = page
            revision.created_by = request.user
            revision.created_ip = request.META.get(settings.WIKI_IP_ADDRESS_META_FIELD, "REMOTE_ADDR")
            revision.parse()
            revision.save()
            return HttpResponseRedirect(binder.page_url(wiki, slug))
    else:
        form = RevisionForm(revision=rev)

    form.fields["content"].help_text = ""

    return render_to_response("wiki/edit.html", {
        "form": form,
        "page": page,
        "revision": rev,
        "can_delete": hookset.can_delete_page(page, request.user)
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
    page_name = "All Pages"
    return render_to_response("wiki/all.html", {
        "page_name": page_name,
        "pages": pages,
    }, context_instance=RequestContext(request))

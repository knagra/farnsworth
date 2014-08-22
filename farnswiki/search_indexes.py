"""
Project: Farnsworth

Authors: Karandeep Singh Nagra and Nader Morshed

Search indexes for the workshift app.
"""

from haystack import indexes

from wiki.models import Page, Revision

class PageIndex(indexes.SearchIndex, indexes.Indexable):
    """ Index for wiki pages. """
    text = indexes.EdgeNgramField(document=True, use_template=True)
    slug = indexes.EdgeNgramField(model_attr='slug', boost=2)

    def get_model(self):
        return Page

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

class RevisionIndex(indexes.SearchIndex, indexes.Indexable):
    """ Index for wiki revisions. """
    text = indexes.EdgeNgramField(document=True, use_template=True)
    content = indexes.EdgeNgramField(model_attr='content', boost=2)
    created_by = indexes.EdgeNgramField(model_attr='created_by')

    def get_model(self):
        return Revision

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

'''
Project: Farnsworth

Author: Karandeep Singh Nagra

Search indexes for the requests app.
'''

from datetime import datetime
from haystack import indexes
from events.models import Event

class EventIndex(indexes.SearchIndex, indexes.Indexable):
    ''' Index for Events. '''
    text = indexes.EdgeNgramField(document=True, use_template=True)
    owner = indexes.EdgeNgramField(model_attr='owner')
    exact_user = indexes.CharField(model_attr='owner', faceted=True)
    title = indexes.EdgeNgramField(model_attr='title', boost=1.125)
    description = indexes.EdgeNgramField(model_attr='description')
    location = indexes.EdgeNgramField(model_attr='location', null=True)
    exact_location = indexes.CharField(model_attr='location', null=True, faceted=True)
    start_time = indexes.DateTimeField(model_attr='start_time')
    end_time = indexes.DateTimeField(model_attr='end_time')
    as_manager = indexes.EdgeNgramField(model_attr='as_manager', null=True)
    exact_manager = indexes.CharField(model_attr='as_manager', null=True, faceted=True)

    def get_model(self):
        return Event

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

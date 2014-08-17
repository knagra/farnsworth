'''
Project: Farnsworth

Author: Karandeep Singh Nagra

Search indexes for the threads app.
'''

from datetime import datetime
from haystack import indexes

from threads.models import Thread, Message

class ThreadIndex(indexes.SearchIndex, indexes.Indexable):
    ''' Index for Threads. '''
    text = indexes.EdgeNgramField(document=True, use_template=True)
    owner = indexes.EdgeNgramField(model_attr='owner')
    exact_user = indexes.CharField(model_attr='owner', faceted=True)
    subject = indexes.EdgeNgramField(model_attr='subject', boost=1.125)
    start_date = indexes.DateTimeField(model_attr='start_date')
    change_date = indexes.DateTimeField(model_attr='change_date')
    
    def get_model(self):
        return Thread
    
    def index_queryset(self, using=None):
        return self.get_model().objects.filter(active=True)

class MessageIndex(indexes.SearchIndex, indexes.Indexable):
    ''' Index for Messages. '''
    text = indexes.EdgeNgramField(document=True, use_template = True)
    owner = indexes.EdgeNgramField(model_attr='owner')
    exact_user = indexes.CharField(model_attr='owner', faceted=True)
    body = indexes.EdgeNgramField(model_attr='body')
    post_date = indexes.DateTimeField(model_attr='post_date')
    
    def get_model(self):
        return Message
    
    def index_queryset(self, using=None):
        return self.get_model().objects.filter(thread__active=True)

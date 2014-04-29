'''
Project: Farnsworth

Author: Karandeep Singh Nagra

Search indexes for the requests app.
'''

from datetime import datetime
from haystack import indexes
from models import Event

class EventIndex(indexes.SearchIndex, indexes.Indexable):
	''' Index for Events. '''
	text = indexes.CharField(document=True, use_template=True)
	owner = indexes.CharField(model_attr='owner')
	title = indexes.CharField(model_attr='title')
	description = indexes.CharField(model_attr='description')
	location = indexes.CharField(model_attr='location', null=True)
	start_time = indexes.DateTimeField(model_attr='start_time')
	end_time = indexes.DateTimeField(model_attr='end_time')
	as_manager = indexes.CharField(model_attr='as_manager', null=True)
	
	def get_model(self):
		return Event
	
	def index_queryset(self, using=None):
		return self.get_model().objects.all()

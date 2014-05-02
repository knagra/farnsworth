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
	text = indexes.NgramField(document=True, use_template=True)
	owner = indexes.NgramField(model_attr='owner')
	title = indexes.NgramField(model_attr='title')
	description = indexes.NgramField(model_attr='description')
	location = indexes.NgramField(model_attr='location', null=True)
	start_time = indexes.DateTimeField(model_attr='start_time')
	end_time = indexes.DateTimeField(model_attr='end_time')
	as_manager = indexes.NgramField(model_attr='as_manager', null=True)
	
	def get_model(self):
		return Event
	
	def index_queryset(self, using=None):
		return self.get_model().objects.all()

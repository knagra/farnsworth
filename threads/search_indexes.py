'''
Project: Farnsworth

Author: Karandeep Singh Nagra

Search indexes for the threads app.
'''

from datetime import datetime
from haystack import indexes
from models import UserProfile, Thread, Message
from farnsworth.settings import ANONYMOUS_USERNAME

class UserProfileIndex(indexes.SearchIndex, indexes.Indexable):
	''' Index for UserProfiles. '''
	text = indexes.EdgeNgramField(document=True, use_template=True)
	user = indexes.EdgeNgramField(model_attr='user')
	exact_user = indexes.CharField(model_attr='user', faceted=True)
	current_room = indexes.EdgeNgramField(model_attr='current_room', null=True)
	exact_location = indexes.CharField(model_attr='current_room', null=True, faceted=True)
	former_rooms = indexes.EdgeNgramField(model_attr='former_rooms', null=True)
	former_houses = indexes.EdgeNgramField(model_attr='former_houses', null=True)
	status = indexes.EdgeNgramField(model_attr='status')
	exact_status = indexes.CharField(model_attr='status', faceted=True)
	
	def get_model(self):
		return UserProfile
	
	def index_queryset(self, using=None):
		return self.get_model().objects.all().exclude(user__username=ANONYMOUS_USERNAME)

class ThreadIndex(indexes.SearchIndex, indexes.Indexable):
	''' Index for Threads. '''
	text = indexes.EdgeNgramField(document=True, use_template=True)
	owner = indexes.EdgeNgramField(model_attr='owner')
	exact_user = indexes.CharField(model_attr='owner', faceted=True)
	subject = indexes.EdgeNgramField(model_attr='subject')
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

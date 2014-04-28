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
	text = indexes.CharField(document=True, use_template=True)
	user = indexes.CharField(model_attr='user')
	current_room = indexes.CharField(model_attr='current_room', null=True)
	former_rooms = indexes.CharField(model_attr='former_rooms', null=True)
	former_houses = indexes.CharField(model_attr='former_houses', null=True)
	status = indexes.CharField(model_attr='status')
	
	def get_model(self):
		return UserProfile
	
	def index_queryset(self, using=None):
		return self.get_model().objects.all().exclude(user__username=ANONYMOUS_USERNAME)

class ThreadIndex(indexes.SearchIndex, indexes.Indexable):
	''' Index for Threads. '''
	text = indexes.CharField(document=True, use_template=True)
	owner = indexes.CharField(model_attr='owner')
	subject = indexes.CharField(model_attr='subject')
	start_date = indexes.DateTimeField(model_attr='start_date')
	change_date = indexes.DateTimeField(model_attr='change_date')
	
	def get_model(self):
		return Thread
	
	def index_queryset(self, using=None):
		return self.get_model().objects.filter(start_date__lte=datetime.now())

class MessageIndex(indexes.SearchIndex, indexes.Indexable):
	''' Index for Messages. '''
	text = indexes.CharField(document=True, use_template = True)
	body = indexes.CharField(model_attr='body')
	post_date = indexes.DateTimeField(model_attr='post_date')
	
	def get_model(self):
		return Message
	
	def index_queryset(self, using=None):
		return self.get_model().objects.filter(post_date__lte=datetime.now())

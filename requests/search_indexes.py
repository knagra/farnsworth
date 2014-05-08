'''
Project: Farnsworth

Author: Karandeep Singh Nagra

Search indexes for the requests app.
'''

from datetime import datetime
from haystack import indexes
from models import Manager, Request, Response, Announcement

class ManagerIndex(indexes.SearchIndex, indexes.Indexable):
	''' Index for Managers. '''
	text = indexes.EdgeNgramField(document=True, use_template=True)
	title = indexes.EdgeNgramField(model_attr='title', boost=1.125)
	incumbent = indexes.EdgeNgramField(model_attr='incumbent')
	exact_user = indexes.CharField(model_attr='incumbent', faceted=True)
	compensation = indexes.EdgeNgramField(model_attr='compensation', null=True)
	duties = indexes.EdgeNgramField(model_attr='duties', null=True)
	email = indexes.EdgeNgramField(model_attr='email', null=True)
	
	def get_model(self):
		return Manager
	
	def index_queryset(self, using=None):
		return self.get_model().objects.all()

class RequestIndex(indexes.SearchIndex, indexes.Indexable):
	''' Index for Requests. '''
	text = indexes.EdgeNgramField(document=True, use_template=True)
	owner = indexes.EdgeNgramField(model_attr='owner')
	exact_user = indexes.CharField(model_attr='owner', faceted=True)
	body = indexes.EdgeNgramField(model_attr='body')
	post_date = indexes.DateTimeField(model_attr='post_date')
	change_date = indexes.DateTimeField(model_attr='change_date')
	
	def get_model(self):
		return Request
	
	def index_queryset(self, using=None):
		return self.get_model().objects.all()

class ResponseIndex(indexes.SearchIndex, indexes.Indexable):
	''' Index for Responses. '''
	text = indexes.EdgeNgramField(document=True, use_template = True)
	owner = indexes.EdgeNgramField(model_attr='owner')
	exact_user = indexes.CharField(model_attr='owner', faceted=True)
	body = indexes.EdgeNgramField(model_attr='body')
	post_date = indexes.DateTimeField(model_attr='post_date')
	request = indexes.EdgeNgramField(model_attr='request')
	
	def get_model(self):
		return Response
	
	def index_queryset(self, using=None):
		return self.get_model().objects.all()

class AnnouncementIndex(indexes.SearchIndex, indexes.Indexable):
	''' Index for Announcements. '''
	text = indexes.EdgeNgramField(document=True, use_template = True)
	manager = indexes.EdgeNgramField(model_attr='manager')
	exact_manager = indexes.CharField(model_attr='manager', faceted=True)
	incumbent = indexes.EdgeNgramField(model_attr='incumbent')
	exact_user = indexes.CharField(model_attr='incumbent', faceted=True)
	body = indexes.EdgeNgramField(model_attr='body')
	post_date = indexes.DateTimeField(model_attr='post_date')
	change_date = indexes.DateTimeField(model_attr='change_date')
	
	def get_model(self):
		return Announcement
	
	def index_queryset(self, using=None):
		return self.get_model().objects.all()

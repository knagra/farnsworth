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
	text = indexes.NgramField(document=True, use_template=True)
	title = indexes.NgramField(model_attr='title')
	incumbent = indexes.NgramField(model_attr='incumbent')
	compensation = indexes.NgramField(model_attr='compensation', null=True)
	duties = indexes.NgramField(model_attr='duties', null=True)
	email = indexes.NgramField(model_attr='email', null=True)
	
	def get_model(self):
		return Manager
	
	def index_queryset(self, using=None):
		return self.get_model().objects.all()

class RequestIndex(indexes.SearchIndex, indexes.Indexable):
	''' Index for Requests. '''
	text = indexes.NgramField(document=True, use_template=True)
	owner = indexes.NgramField(model_attr='owner')
	body = indexes.NgramField(model_attr='body')
	post_date = indexes.DateTimeField(model_attr='post_date')
	change_date = indexes.DateTimeField(model_attr='change_date')
	
	def get_model(self):
		return Request
	
	def index_queryset(self, using=None):
		return self.get_model().objects.all()

class ResponseIndex(indexes.SearchIndex, indexes.Indexable):
	''' Index for Responses. '''
	text = indexes.NgramField(document=True, use_template = True)
	owner = indexes.NgramField(model_attr='owner')
	body = indexes.NgramField(model_attr='body')
	post_date = indexes.DateTimeField(model_attr='post_date')
	request = indexes.NgramField(model_attr='request')
	
	def get_model(self):
		return Response
	
	def index_queryset(self, using=None):
		return self.get_model().objects.all()

class AnnouncementIndex(indexes.SearchIndex, indexes.Indexable):
	''' Index for Announcements. '''
	text = indexes.NgramField(document=True, use_template = True)
	manager = indexes.NgramField(model_attr='manager')
	incumbent = indexes.NgramField(model_attr='incumbent')
	body = indexes.NgramField(model_attr='body')
	post_date = indexes.DateTimeField(model_attr='post_date')
	change_date = indexes.DateTimeField(model_attr='change_date')
	
	def get_model(self):
		return Announcement
	
	def index_queryset(self, using=None):
		return self.get_model().objects.all()

'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

from datetime import datetime

from django import forms
from django.utils.timezone import utc

from base.models import UserProfile
from threads.models import Thread, Message

class ThreadForm(forms.Form):
	''' Form to post a new thread. '''
	subject = forms.CharField(widget=forms.TextInput(), required=True)
	body = forms.CharField(widget=forms.Textarea())

	def __init__(self, *args, **kwargs):
		self.profile = kwargs.pop('profile')
		super(ThreadForm, self).__init__(*args, **kwargs)

	def save(self):
	   thread = Thread(
		   owner=self.profile,
		   subject=self.cleaned_data['subject'],
		   number_of_messages=1,
		   active=True,
		   )
	   thread.save()
	   message = Message(
		   body=self.cleaned_data['body'],
		   owner=self.profile,
		   thread=thread,
		   )
	   message.save()

class MessageForm(forms.Form):
	''' Form to post a new message. '''
	thread_pk = forms.IntegerField(widget=forms.HiddenInput())
	body = forms.CharField(widget=forms.Textarea())

	def __init__(self, *args, **kwargs):
		self.profile = kwargs.pop('profile')
		super(MessageForm, self).__init__(*args, **kwargs)

	def clean_thread_pk(self):
		try:
			thread = Thread.objects.get(pk=self.cleaned_data["thread_pk"])
		except Thread.DoesNotExist:
			raise ValidationError("Thread does not exist.")
		return thread

	def save(self):
		thread = self.cleaned_data["thread_pk"]
		message = Message(
			body=self.cleaned_data["body"],
			owner=self.profile,
			thread=thread,
			)
		message.save()
		thread.number_of_messages += 1
		thread.change_date = datetime.utcnow().replace(tzinfo=utc)
		thread.save()

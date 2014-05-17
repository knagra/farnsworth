'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

from django import forms

from base.models import UserProfile
from threads.models import Thread, Message

class ThreadForm(forms.Form):
	''' Form to post a new thread. '''
	subject = forms.CharField(max_length=300, widget=forms.TextInput(attrs={'size':'100'}))
	body = forms.CharField(widget=forms.Textarea())

class MessageForm(forms.Form):
	''' Form to post a new message. '''
	thread_pk = forms.IntegerField(widget=forms.HiddenInput())
	body = forms.CharField(widget=forms.Textarea())

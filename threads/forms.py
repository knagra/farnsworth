'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

from datetime import datetime

from django import forms
from django.utils.timezone import utc

from threads.models import Thread, Message

class ThreadForm(forms.ModelForm):
    ''' Form to post a new thread. '''
    body = forms.CharField(widget=forms.Textarea())

    class Meta:
        model = Thread
        fields = ("subject",)

    def __init__(self, *args, **kwargs):
        self.profile = kwargs.pop('profile')
        super(ThreadForm, self).__init__(*args, **kwargs)

    def save(self):
        thread = super(ThreadForm, self).save(commit=False)
        thread.owner = self.profile
        thread.save()
        Message.objects.create(
            body=self.cleaned_data['body'],
            owner=self.profile,
            thread=thread,
            )
        return thread

class MessageForm(forms.ModelForm):
    ''' Form to post a new message. '''
    class Meta:
        model = Message
        fields = ("body",)

    def __init__(self, *args, **kwargs):
        self.profile = kwargs.pop('profile')
        self.thread = kwargs.pop('thread')
        super(MessageForm, self).__init__(*args, **kwargs)

    def save(self):
        message = super(MessageForm, self).save(commit=False)
        message.owner = self.profile
        message.thread = self.thread
        message.save()

        self.thread.number_of_messages += 1
        self.thread.change_date = datetime.utcnow().replace(tzinfo=utc)
        self.thread.save()

        return message

class EditThreadForm(forms.ModelForm):
    label = "edit"
    display = "Edit"
    button = "success"
    glyph = "comment"
    class Meta:
        model = Thread
        fields = ("subject",)

class DeleteMessageForm(forms.ModelForm):
    label = "delete"
    display = "Delete"
    button = "danger"
    glyph = "fire"

    class Meta:
        model = Message
        fields = ()

    def save(self):
        message = super(DeleteMessageForm, self).save()
        thread = message.thread
        message.delete()
        thread.number_of_messages -= 1
        if thread.number_of_messages == 0:
            thread.delete()
        else:
            thread.save()
            return thread

class EditMessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ("body",)

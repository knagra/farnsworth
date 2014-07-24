'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

from django import forms
from django.forms.models import BaseModelFormSet, modelformset_factory

from elections.models import Petition, PetitionComment, \
    Poll, PollSettings, PollQuestion, PollChoice, \
    PollAnswer

class PetitionForm(forms.ModelForm):
    class Meta:
        model = Petition
        fields = ("title", "description", "end_date")

    def __init__(self, *args, **kwargs):
        self.profile = kwargs.pop('profile')
        super(PetitionForm, self).__init__(*args, **kwargs)

    def save(self):
        petition = super(PetitionForm, self).save(commit=False)
        petition.owner = self.profile
        petition.save()

class PetitionCommentForm(forms.ModelForm):
    class Meta:
        model = PetitionComment
        fields = ("body",)

    def __init__(self, *args, **kwargs):
        self.petition = kwargs.pop('petition')
        self.profile = kwargs.pop('profile')
        super(PetitionCommentForm, self).__init__(*args, **kwargs)

    def save(self):
        comment = super(PetitionCommentForm, self).save(commit=False)
        comment.user = self.profile
        comment.petition = self.petition
        comment.save()

class PetitionSignatureForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.profile = kwargs.pop('profile')
        self.petition = kwargs.pop('petition')
        super(PetitionSignatureForm, self).save(*args, **kwargs)

    def save(self):
        if self.profile in self.petition.signatures.all():
            self.petition.signatures.remove(self.profile)
        else:
            self.petition.signatures.add(self.profile)
        self.petition.save()
        return self.petition

class PollForm(form.ModelForm):
    class Meta:
        model = Poll
        fields = (
            "title",
            "description",
            "close_date",
            "anonymity_allowed",
            "alumni_allowed",
            )

    def __init__(self, *args, **kwargs):
        super(PollForm, self).__init__(*args, **kwargs)
        if 'election' in kwargs:
            self.election = True
            self.fields.pop('anonymity_allowed')
            self.fields.pop('alumni_allowed')
        else:
            self.election = False
        self.profile = kwargs.pop('profile')

    def save(self):
        poll = super(PollForm, self).save(commit=False)
        if self.election:
            poll.election = True
            poll.anonymity_allowed = True
        poll.save()

class PollQuestionForm(models.Model):
    choice_text = forms.CharField(
        widget=forms.Textarea,
        required=False,
        help_text="One line per option.",
        )

    class Meta:
        model = PollQuestion
        fields = ("body", "question_type", "write_ins_allowed")

    def is_valid(self):
        if not super(PollQuestionForm, self).is_valid():
            return False
        if self.cleaned_data['question_type'] == PollQuestion.CHOICE \
            or self.cleaned_data['question_type'] == PollQuestion.RANK \
            and not self.cleaned_data['choice_text']:
                

class BasePollQuestionFormSet(BaseModelFormSet):
    def __init__(self, *args, **kwargs):
        

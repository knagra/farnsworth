"""
Project: Farnsworth

Authors: Karandeep Singh Nagra and Nader Morshed
"""

from django.contrib import admin
from elections.models import Petition, PetitionComment, \
    Poll, PollSettings, PollQuestion, PollChoice, PollAnswer

for p in [Petition, PetitionComment, Poll, PollSettings,
  PollQuestion, PollChoice, PollAnswer]:
    admin.site.register(p)

'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

import re

from django.shortcuts import redirect
from django.contrib import messages
from django.core.urlresolvers import reverse

from social.pipeline.partial import partial

from base.models import UserProfile, ProfileRequest

def _get_first_last(details):
	"""
	Gets a user's first and last name from details.
	"""
	if "first_name" in details and "last_name" in details:
		return details["first_name"], details["last_name"]
	elif "first_name" in details:
		lst = details["first_name"].rsplit(" ", 1)
		if len(lst) == 2:
			return lst
		else:
			return lst[0], ""
	elif "last_name" in details:
		return "", details["last_name"]

	return "", ""

@partial
def request_user(strategy, details, user=None, request=None, is_new=False, uid=None, **kwargs):
	if user:
		return
	elif is_new:
		username = re.sub("[^a-zA-Z0-9_]", "_", details["username"].lower())

		try:
			ProfileRequest.objects.get(username=username)
		except ProfileRequest.DoesNotExist:
			pass
		else:
			messages.add_message(request, messages.WARNING,
					     "Profile request already submitted")
			return redirect(reverse('request_profile'))

		first, last = _get_first_last(details)
		email = details["email"]
		pr = ProfileRequest(
			username=username,
			first_name=first, last_name=last,
			email=email,
			affiliation=UserProfile.STATUS_CHOICES[0][0],
			provider=strategy.backend.name,
			uid=uid,
			)
		pr.save()

		messages.add_message(request, messages.SUCCESS,
				     "Your account request has been submitted.")
		return redirect(reverse('request_profile'))

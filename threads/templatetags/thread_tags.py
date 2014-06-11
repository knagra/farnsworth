'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

from random import choice

from django import template

from utils.variables import ANONYMOUS_USERNAME, SUBTEXTS_404

register = template.Library()

@register.filter
def display_user(value, arg):
	''' Return 'You' if value is equal to arg.
		Parameters:
			value should be a userprofile
			arg should be another user.
		Ideally, value should be a userprofile from an object and arg the user logged in.
	'''
	if value.user == arg and arg.username != ANONYMOUS_USERNAME:
		return "You"
	else:
		return value.user.get_full_name()

@register.filter
def show_404_subtext(value):
	''' Return a random string to show underneath the 404 title in the 404 page.
		Parameters:
			value is anything at all; it's not actually used in this function at all.
	'''
	return choice(SUBTEXTS_404)

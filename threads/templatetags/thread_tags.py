'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

from django import template

register = template.Library()

@register.filter
def display_user(value, arg):
	''' Return 'You' if value is equal to arg.
		Parameters:
			value should be a userprofile
			arg should be another user.
		Ideally, value should be a userprofile from an object and arg the user logged in.
	'''
	if value.user == arg:
		return "You"
	else:
		return value.user.get_full_name()

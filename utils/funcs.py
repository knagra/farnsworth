'''
Project: Farnsworth

Author: Karandeep Singh Nagra

A collection of functions used elsewhere in Farnsworth.
'''

import re

from django import forms

if hasattr(forms, "utils"):
	ErrorList = forms.utils.ErrorList
else:
	ErrorList = forms.util.ErrorList

def verify_username(username):
	''' Verify a potential username.
	Parameters:
		username is the potential username
	Returns True if username contains only characters a through z, A through Z, 0 through 9, the underscore or hyphen character; returns false otherwise.
	'''
	return not bool(re.compile(r'[^a-zA-Z0-9_\-]').search(username))

def verify_name(name):
	''' Verify a potential first or last name.  Currently not used as it is Anglo-centric.
	Parameters:
		name is the potential first or last name
	Returns True if name doesn't contain ", <, >, &, ; returns false otherwise.
	'''
	return bool(re.compile(r"[^a-zA-Z']").search(name))

def verify_url(potential_url):
	''' Verify that potential_url can be converted to a URL by lowercasing and replacing characters as specified in convert_to_url.
	Parameters:
		potential_url is a potential name, title, etc. to be used in a URL.
	Returns True if potential_url only contains characters a through z, A through Z, 0 through 9, space, or selected other characters.
	'''
	return not bool(re.compile(r"[^a-zA-Z0-9 _&'?$^%@!#*()=+;:|/.,\-]").search(potential_url))

def convert_to_url(actual):
	''' Convert a string into a URL-usable word.
	Parameters:
		actual is a string to be converted into a URL-usable word.
	Returns a string after the following operations:
		lowercase name
		replace the space character by underscore
		remove the characters '?$^%@!#*()=+\;:/.,
		replace the character & by the string 'and'
	'''
	return re.sub("['?$^%@!#*()=+;:|/.,]", '', actual.lower().replace(' ', '_').replace('&', 'and'))

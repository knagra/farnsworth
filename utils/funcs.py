'''
Project: Farnsworth

Author: Karandeep Singh Nagra

A collection of functions used elsewhere in Farnsworth.
'''

import re

def verify_username(username):
	''' Verify a potential username.
	Parameters:
		username is the potential username
	Returns True if username contains only characters a through z, A through Z, 0 through 9, or the underscore character; returns false otherwise.
	'''
	return not bool(re.compile(r'[^a-zA-Z0-9_]').search(username))

def verify_name(name):
	''' Verify a potential first or last name.
	Parameters:
		name is the potential first or last name
	Returns True if name doesn't contain ", <, >, &, ; returns false otherwise.
	'''
	return bool(re.compile(r"[^a-zA-Z']").search(name))

def verify_url(potential_url):
	''' Verify that potential_url can be converted to a URL by lowercasing and replacing spaces by underscores.
	Parameters:
		potential_url is a potential name, title, etc. to be used in a URL.
	Returns True if username contains only characters a through z, A through Z, 0 through 9, or the space character; returns false otherwise.
	'''
	return not bool(re.compile(r'[^a-zA-Z0-9 ]').search(potential_url))

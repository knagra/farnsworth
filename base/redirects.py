'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

def red_ext(request, message=None):
    '''
    The external landing.
    Also a convenience function for redirecting users who don't have site access to the external page.
    Parameters:
        request - the request in the calling function
        message - a message from the caller function
    '''
    if message:
        messages.add_message(request, messages.ERROR, message)
    return HttpResponseRedirect(reverse('external'))

def red_home(request, message=None):
    '''
    Convenience function for redirecting users who don't have access to a page to the home page.
    Parameters:
        request - the request in the calling function
        message - a message from the caller function
    '''
    if message:
        messages.add_message(request, messages.ERROR, message)
    return HttpResponseRedirect(reverse('homepage'))

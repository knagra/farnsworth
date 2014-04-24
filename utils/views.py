'''
Project: Farnsworth

Author: Karandeep Singh Nagra

Utilities for administration.
'''

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from farnsworth.settings import ANONYMOUS_USERNAME
# Standard messages:
from farnsworth.settings import ANONYMOUS_DENIED, ANONYMOUS_LOGIN
from threads.views import red_home
from django.contrib import messages


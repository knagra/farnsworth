'''
Project: Farnswroth

Author: Karandeep Singh Nagra
'''

from django.contrib import admin
from requests.models import Manager, Request, Response

admin.site.register(Manager)
admin.site.register(Request)
admin.site.register(Response)

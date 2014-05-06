# Django settings for farnsworth project.

'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

import os.path
from django.conf import global_settings

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
	# This top admin is used on all pages as the support contact.
	('Karandeep Singh Nagra', 'karandeepsnagra@gmail.com'),
)

MANAGERS = ADMINS

BASE_URL = "/farnsworth"

# Name of the house
house = "African-American Theme House"

# Short name of the house
short_house = "Afro"

# Max number of threads loaded in member_forums.
max_threads = 20

# Max number of messages loaded for each thread.
max_messages = 4

# Max number of requests loaded in requests_view.
max_requests = 30

# Max number of responses loaded for each request.
max_responses = 4

# Max number of announcements loaded for home page.
home_max_announcements = 5

# Max number of threads loaded for home page.
home_max_threads = 15

# The anonymous username.
ANONYMOUS_USERNAME = "spineless"

# Standard messages sent to clients on errors.
MESSAGES = {
	'ADMINS_ONLY': "The domain /custom_admin/ is restricted to admins.",
	'NO_PROFILE': "A profile for you could not be found.  Please contact a site admin.",
	'UNKNOWN_FORM': "Your post request could not be processed.  Please contact a site admin.",
	'MESSAGE_ERROR': "Your message post was not successful.  Please try again.",
	'THREAD_ERROR': "Your thread post was not successful.  Both subject and body are required.  Please try again.",
	'USER_ADDED': "User {username} has successfully added.",
	'PREQ_DEL': "Profile request by {first_name} {last_name} for username {username} successfully deleted.",
	'USER_PROFILE_SAVED': "User {username}'s profile has been successfully updated.",
	'USER_PW_CHANGED': "User {username}'s password has been successfully changed.",
	'EVENT_ERROR': "Your event post was not successful.  Please check for errors and try again.",
	'RSVP_ADD': "You've been successfully added to the list of RSVPs for {event}.",
	'RSVP_REMOVE': "You've been successfully removed from the list of RSVPs for {event}.",
	'EVENT_UPDATED': "Event {event} successfully updated.",
	'REQ_CLOSED': "Request successfully marked closed.",
	'REQ_FILLED': "Request successfully marked filled.",
	'SPINELESS': "You cannot modify the anonymous user profile.",
	'ANONYMOUS_EDIT': "THIS IS THE ANONYMOUS USER PROFILE.  IT IS HIGHLY RECOMMENDED THAT YOU NOT MODIFY IT.",
	'ANONYMOUS_DENIED': "Only superadmins are allowed to login the anonymous user or end the anonymous session.",
	'ANONYMOUS_LOGIN': "You have successfully logged out and started an anonymous session on this machine.",
	'ANONYMOUS_SESSION_ENDED': "You have successfully ended the anonymous session on this machine.",
	'RECOUNTED': "Thread messages and request responses successfully recounted.",
	'ALREADY_PAST': "This event has already passed.  You can no longer RSVP to this event.",
}

# Add the context that populates a few variables used on every page in the site.
TEMPLATE_CONTEXT_PROCESSORS = global_settings.TEMPLATE_CONTEXT_PROCESSORS + ("requests.views.add_context",)

# List of time formats accepted by event forms.
time_formats = ['%m/%d/%Y %I:%M %p', '%m/%d/%Y %I:%M:%S %p', '%Y-%m-%d %H:%M:%S']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(os.path.dirname(__file__), 'farnsworth.db').replace('\\', '/'),
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/Los_Angeles'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# In this case, the directory
MEDIA_ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'media/').replace('\\', '/')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static/').replace('\\', '/')

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '*ebg4v3j9)se)=idd8v50fbi&kym9*ki@8&z-yy&sv%6!chc=c'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'farnsworth.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'farnsworth.wsgi.application'

TEMPLATE_DIRS = (
	os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates').replace('\\', '/'),
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

INSTALLED_APPS = (
	'django.contrib.auth',
	'django.contrib.contenttypes',
	'django.contrib.sessions',
	'django.contrib.sites',
	'django.contrib.messages',
	'django.contrib.staticfiles',
	'threads',
	'events',
	'requests',
	'bootstrapform',
	'south',
	'haystack',
	'django.contrib.admin',
	'django.contrib.admindocs',
)

LOGIN_URL = BASE_URL + "/login/"
LOGOUT_URL = BASE_URL + "/logout/"
LOGIN_REDIRECT_URL = BASE_URL

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

# Haystack search backend setting.
HAYSTACK_CONNECTIONS = {
	'default': {
		'ENGINE': 'haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine',
		'URL': 'http://127.0.0.1:9200/',
		'INDEX_NAME': 'haystack',
	},
}

HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.RealtimeSignalProcessor'

HAYSTACK_SEARCH_RESULTS_PER_PAGE = 50

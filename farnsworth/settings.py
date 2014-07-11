# Django settings for farnsworth project.

'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

import os.path
import sys
from django.conf import global_settings

try:
	from farnsworth.house_settings import *
except ImportError:
	pass

DEBUG = False
# TEMPLATE_DEBUG = DEBUG

ADMINS = (
	# This top admin is used on all pages as the support contact.
	# The e-mail for this admin is used as the reply-to e-mail for e-mails
	# if sending e-mails is enabled.
	(SHORT_HOUSE_NAME + " Network Manager", HOUSE_ABBREV + "nm@bsc.coop"),
)

MANAGERS = ADMINS

BASE_URL = "/" + SHORT_HOUSE_NAME.lower()

# Name of the house
HOUSE = HOUSE_NAME

# Short name of the house. Alphabet only; otherwise, search won't work.
SHORT_HOUSE = SHORT_HOUSE_NAME

try:
	NETWORK_MANAGER_PASSWORD
except NameError:
	NETWORK_MANAGER_PASSWORD = None

if NETWORK_MANAGER_PASSWORD:
	# Whether e-mails are sent for certain events.
	# Currently, this includes approval or deletion of profile requests,
	# and profile request submission.
	# Change this setting to True and fill out the e-mail settings below
	# to send e-mails.
	SEND_EMAILS = True

	# E-mail settings.  Enter your username and password to use Gmail.
	# You can also use a different SMTP server by changing these settings.
	EMAIL_USE_TLS = True
	EMAIL_HOST = 'smtp.gmail.com'
	EMAIL_HOST_USER = HOUSE_ABBREV + "nm@bsc.coop"
	EMAIL_HOST_PASSWORD = NETWORK_MANAGER_PASSWORD
	EMAIL_PORT = 587
else:
	SEND_EMAILS = False

# E-mail blacklist.  E-mails will not be sent to these addresses no matter what.
# Add e-mails here as strings separated by commas, to prevent the site from sending e-mails
# to select addresses.  Here's an example:
# EXAMPLE_EMAIL_BLACKLIST = ('karandeepsnagra@gmail.com',
#	'some_user@some_domain.com',
#	)
EMAIL_BLACKLIST = ()

# Max number of threads loaded in member_forums.
MAX_THREADS = 20

# Max number of messages loaded for each thread in member_forums.
MAX_MESSAGES = 4

# Max number of requests loaded in requests_view.
MAX_REQUESTS = 30

# Max number of responses loaded for each request.
MAX_RESPONSES = 4

# How old, in days, an announcement should be before it's automatically excluded
# from being displayed on the homepage and in the manager announcements page.
# Pinned announcements will be displayed anyway.
ANNOUNCEMENT_LIFE = 4

# Max number of threads loaded for home page.
HOME_MAX_THREADS = 15

# Add the context that populates a few variables used on every page in the site.
TEMPLATE_CONTEXT_PROCESSORS = global_settings.TEMPLATE_CONTEXT_PROCESSORS + ("base.views.add_context",)

try:
	ENABLE_OAUTH
except NameError:
	ENABLE_OAUTH = None

if ENABLE_OAUTH:
	TEMPLATE_CONTEXT_PROCESSORS += (
		'social.apps.django_app.context_processors.backends',
	)

try:
	POSTGRES_PASSWORD
except NameError:
	POSTGRES_PASSWORD = None

if POSTGRES_PASSWORD:
	# PostgreSQL setup
	DATABASES = {
		'default': {
			'ENGINE': 'django.db.backends.postgresql_psycopg2',
			'NAME': SHORT_HOUSE_NAME.lower(),
			'USER': SHORT_HOUSE_NAME.lower() + '_admin',
			'PASSWORD': POSTGRES_PASSWORD,
			'HOST': 'localhost',
			'PORT': '',
		},
	}
else:
	# SQLite3 setup
	DATABASES = {
		'default': {
			'ENGINE': 'django.db.backends.sqlite3',
			'NAME': os.path.join(os.path.dirname(__file__), 'farnsworth.db').replace('\\', '/'),
			'USER': '',
			'PASSWORD': '',
			'HOST': '',
			'PORT': '',
		},
	}

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
try:
	SITE_DOMAIN
except NameError:
	SITE_DOMAIN = None

if SITE_DOMAIN:
	# Matches SITE_DOMAIN and "*.SITE_DOMAIN"
	ALLOWED_HOSTS = ["." + SITE_DOMAIN]
else:
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
#	'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
	'django.template.loaders.filesystem.Loader',
	'django.template.loaders.app_directories.Loader',
#	'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
	'django.middleware.common.CommonMiddleware',
	'django.contrib.sessions.middleware.SessionMiddleware',
	'django.middleware.csrf.CsrfViewMiddleware',
	'django.contrib.auth.middleware.AuthenticationMiddleware',
	'django.contrib.messages.middleware.MessageMiddleware',
	'django.middleware.clickjacking.XFrameOptionsMiddleware',
	'social.apps.django_app.middleware.SocialAuthExceptionMiddleware',
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
	'base',
	'threads',
	'events',
	'managers',
	'bootstrapform',
	'haystack',
	'django.contrib.admin',
	'django.contrib.admindocs',
	'social.apps.django_app.default',
)

AUTHENTICATION_BACKENDS = (
	'django.contrib.auth.backends.ModelBackend',
)

try:
	ENABLE_OAUTH
except NameError:
	ENABLE_OAUTH = False

if ENABLE_OAUTH:
	try:
		if SOCIAL_AUTH_FACEBOOK_KEY and SOCIAL_AUTH_FACEBOOK_SECRET:
			AUTHENTICATION_BACKENDS = ('social.backends.facebook.FacebookOAuth2',) + AUTHENTICATION_BACKENDS
	except NameError:
		pass

	try:
		if SOCIAL_AUTH_GITHUB_KEY and SOCIAL_AUTH_GITHUB_SECRET:
			AUTHENTICATION_BACKENDS = ('social.backends.github.GithubOAuth2',) + AUTHENTICATION_BACKENDS
	except NameError:
		pass

	try:
		if SOCIAL_AUTH_GOOGLE_OAUTH2_KEY and SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET:
			AUTHENTICATION_BACKENDS = ('social.backends.google.GoogleOAuth2',) + AUTHENTICATION_BACKENDS
	except NameError:
		pass

SOCIAL_AUTH_FACEBOOK_SCOPE = ['email', 'public_profile']
SOCIAL_AUTH_GITHUB_SCOPE = ['user:email']
SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = ['email']

LOGIN_URL = BASE_URL + "/login/"
LOGOUT_URL = BASE_URL + "/logout/"
LOGIN_REDIRECT_URL = BASE_URL
LOGIN_ERROR_URL = BASE_URL

SOCIAL_AUTH_PIPELINE = (
	'social.pipeline.social_auth.social_details',
	'social.pipeline.social_auth.social_uid',
	'social.pipeline.social_auth.auth_allowed',
	'social.pipeline.social_auth.social_user',
	'social.pipeline.user.get_username',
	'base.pipeline.request_user',
)

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
		'elasticsearch': {
			'handlers': ['mail_admins'],
			'level': 'ERROR',
			'propagate': True,
		}
	}
}

# Haystack search backend setting.
HAYSTACK_CONNECTIONS = {
	'default': {
		'ENGINE': 'haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine',
		'URL': 'http://localhost:9200/',
		'INDEX_NAME': SHORT_HOUSE_NAME.lower(),
	},
}

HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.RealtimeSignalProcessor'
HAYSTACK_SEARCH_RESULTS_PER_PAGE = 50

if 'test' in sys.argv:
	PASSWORD_HASHERS = (
		'django.contrib.auth.hashers.MD5PasswordHasher',
	)
	DATABASES['default'] = {
		'ENGINE': 'django.db.backends.sqlite3',
		}
	HAYSTACK_CONNECTIONS['default'] = {
		'ENGINE': 'haystack.backends.simple_backend.SimpleEngine',
		}

try:
	from farnsworth.local_settings import *
except ImportError:
	pass

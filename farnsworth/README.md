### Core Module - `/farnsworth/`
This directory contains the settings (`settings.py`) and the main set of URLs for the application (`urls.py`),
which covers URLs for the base, threads, and managers applications, but does not contain URLs for other applications.
Settings are divided into `settings.py`, `local_settings.py`, and `house_settings.py.example`,
which should be modified and renamed to `house_settings.py` upon installation.

Not all settings are covered here.

#### Settings
##### `/farnsworth/house_settings.py.example`
This file is imported into `/farnsworth/settings.py` and variables from it are used to populate fields in that file.
All of your house-specific settings will go in here.
* `SECRET_KEY` - Secret Django key.  You can generate one and paste it in.  Check the file for instructions.
* `HOUSE_NAME` - Full name of the house.
* `SHORT_HOUSE_NAME` - Short name of the house.
* `HOUSE_ABBREV` - Abbreviation for the house, used for creating NM e-mail address in `farnsworth.settings.ADMINS`

##### `/farnsworth/settings.py`
* `DEBUG` - Whether debug messages are printed to browsers.  Default = `False`
* `ADMINS` - Tuple of admins for the site.  Django will send debug messages to these e-mail addresses when error occur.
The first tuple in this field is also used to display contact information in the footer of all pages,
in the `/base/templates/base.html` template.
* `EMAIL_BLACKLIST` - A list of e-mails never to send e-mails to.
* `MAX_THREADS` - Maximum threads to load in `member_forums`.
* `MAX_MESSAGES` - Maximum messages to load for each thread in `member_forums`.
* `MAX_REQUESTS` - Maximum requests to load in `requests_view`.
* `MAX_RESPONSES` - Maximum responses to load for each request in `requests_view`.
* `ANNOUNCEMENT_LIFE` - How old, in days, an announcement should be before it's automatically excluded from being
displayed on the homepage and the manager announcements page.
* `HOME_MAX_THREADS` - Maximum number of threads to load for homepage.
* `HAYSTACK_CONNECTIONS` - Connection settings for Django-Haystack for indexing and searching.
    * `ENGINE`: The engine to use. Default: Elasticsearch, `'haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine'`
    * `URL`: URL to connect to for the Elasticsearch server/cluster.
    * `INDEX_NAME`: The name of the index. Default: `SHORT_HOUSE_NAME.lower()`

##### `/farnsworth/local_settings.py`
This file is imported into the `settings.py` file at the very end.
You can add any local settings here to override settings in `/farnsworth/settings.py`.

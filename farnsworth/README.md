### Core Module - `/farnsworth/`
This directory contains the settings (`settings.py`) and the main set of URLs for the application (`urls.py`),
which covers URLs for the base, threads, and managers applications, but does not contain URLs for other applications.
Settings are divided into `settings.py`, `local_settings.py`, and `house_settings.py.example`,
which should be modified and renamed to `house_settings.py` upon installation.

#### Settings
##### `/farnsworth/settings.py`
* `DEBUG` - Whether debug messages are printed to browsers.  Default = `False`
* `ADMINS` - Tuple of admins for the site.  Django will send debug messages to these e-mail addresses when error occur.
The first tuple in this field is also used to display contact information in the footer of all pages,
in the `/base/templates/base.html` template.

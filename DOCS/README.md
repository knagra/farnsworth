## Logical Structure
Each application in Farnsworth contains certain models, indexes for a select subset of those models, select views,
and static &amp; template files for those views.
Almost all of the base application (`/base/`) is independent of the other applications but dependent on
the `/farnsworth/` directory, which contains settings, URLs, and `wsgi.py`.
However, the `homepage_view` function is dependent on all the other applications.
This is acceptable as it causes no import loops for models.
The threads application (`/threads/`) is dependent on the base application.
The managers application (`/managers/`) is dependent on the base application.
The events application (`/events/`) is dependent on the base and managers applications.

### Root Directory - `/`
This directory contains information about Farnsworth and some utilities, such as `manage.py` to manage the Django
application, `pull.sh` to pull changes to all branches on Kingman's web server, `merge_and_push.sh` to merge
and push changes from master into the other branches on Kingman's server, etc.
This directory also contains all the other applications required for Farnsworth.

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


### Base Application - `/base/`
User profiles and management and the homepage and external view.
Also includes decorators, common css files, base template, 404 template, and base search template.

#### Models - `/base/models.py`
* `UserProfile` - A user's profile, contains extra data: phone number, visiblity settings, etc.
* `ProfileRequest` - Model for a request for a profile on the site.

#### Forms - `/base/forms.py`
* `ProfileRequestForm` - Form to request a user profile on the site.
* `AddUserForm` - Form for an admin (superuser) to add a new user to the site.
* `DeleteUserForm` - Form for an admin to delete a user from the site.
* `ModifyUserForm` - Form for an admin to modify a user's profile on the site.
* `ModifyProfileRequestForm` - Form for an admin to approve or delete a request for a profile on the site.
* `UpdateProfileForm` - Form for a user to update her/his profile on the site.
* `LoginForm` - Form for a user to login to the site.

#### Views - `/base/views.py`
* `landing_view` - View of the landing to the site. URL: `/`
* `homepage_view` - View of the homepage, with several key pieces of information. URL: `/`
* `help_view` - View of helpful information about the site and how to use it. URL: `/help/`
* `site_map_view` - View of all the various pages accessible by the logged in user.  URL: `/site_map/`
* `my_profile_view` - View for a logged in user to modify her/his profile. URL: `/profile/`
* `login_view` - View for a user to login. URL: `/login/`
* `logout_view` - Log the current user out and redirect to `/`. URL: `/logout/`
* `member_directory_view` - Show tables of residents, boarders, and alumni. URL: `/member_directory/`
* `member_profile_view` - View to see another member's profile. URL: `/profile/<username>/`
* `request_profile_view` - View to request a new user profile on the site. URL: `/request_profile/`
* `manage_profile_requests_view` - View to see a table of all existing profile requests. URL: `/custom_admin/profile_requests/`
* `modify_profile_request_view` - View for an admin to approve or delete a request for a profile. URL: `/custom_admin/profile_requests/<request_pk>/`
* `custom_manage_users_view` - View for an admin to see tables of users and relevant information. URL: `/custom_admin/manage_users/`
* `custom_modify_user_view` - View for an admin to modify a user's profile. URL: `/custom_admin/manage_users/<username>/`
* `custom_add_user_view` - View for an admin to add a new user. URL: `/custom_admin/add_user/`
* `utilities_view` - View of various utilities available in the site. URL: `/custom_admin/utilities/`
* `reset_pw_view` - View for a user to enter an e-mail address to reset password. URL: `/reset/`
* `reset_pw_confirm_view` - View for a user to set a new password using a token generated and e-mailed by `reset_pw_view`. URL: `/reset/<token>/`

#### CSS - `/base/static/ui/css/`
* `base.css`
* `bootstrap-datetimepicker.min.css`
* `content.css`
* `custom_add_user.css`
* `custom_manage_users.css`
* `custom_modify_user.css`
* `external.css`
* `homepage.css`
* `manage_profile_requests.css`
* `member_directory.css`
* `my_profile.css`
* `search.css`
* `site_map.css`
* `utilities.css`

#### Decorators - `/base/decorators.py`
* `profile_required` - Used for views where a user must have a UserProfile to access the view.
* `admin_required` - Used for views where a user must be an admin (`user.is_superuser == True`) to access the view.
* `president_admin_required` - Used for views where a user must hold a president position to access the view.

#### Etc.
* `base.views.add_context` - Function; adds variables to be sent to templates that are recurring and required by all or most templates.
* `base.views._get_oauth_providers` - Function; grab all OAuth providers that are setup for the given installation of Farnsworth.
* `/base/templates/search/search.html` - Template; the base search view, which uses `include`s to include other templates.
* `/base/templates/base.html` - Template; base template that other templates extend for views.
* `/base/templates/404.html` - Template; displays `404 - Page Not Found` message with a randomly selected blurb.


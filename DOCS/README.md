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
which covers URLs for the base and managers applications, but does not contain URLs for other applications.
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

### Threads Application - /threads/
Community threads, forums, messages.  Includes URLs for the threads application.

#### URLs - `/threads/urls.py`
* `/threads/` - View: `member_forums_view`, name: `member_forums`
* `/threads/<thread_pk>/` - View: `thread_view`, name: `view_thread`
* `/threads/list/` - View: `list_all_threads_view`, name: `list_all_threads`
* `/profile/<username>/threads/` - View: `list_user_threads_view`, name: `list_user_threads`
* `/profile/<username/messages/` - View: `list_user_messages_view`, name: `list_user_messages`

#### Models - `/threads/models.py`
* `Thread` - Anchor and grouping as "threads" for messages.
* `Message` - An individual message in a thread.

#### Forms - `/threads/forms.py`
* `ThreadForm` - Form to create a new thread.
* `MessageForm` - Form to create a new message in a thread.

#### Views - `/threads/views.py`
* `member_forums_view` - Shows recent threads in semi-expanded view (some recent messages showing).
* `list_user_threads_view` - Lists threads owned (started) by a given user.
* `list_all_threads_view` - Lists all threads in the database.
* `thread_view` - View of an individual thread.

#### CSS - `/threads/static/ui/css/`
* `list_threads.css`
* `threads.css`

#### Template tags - `/threads/templatetags/thread_tags.py`
* `display_user` - Convenience function for displaying 'You' or the username of a user given the logged in user.
* `show_404_subtext` - Returns randomly picked choice from `utils.variables.SUBTEXTS_404`

### Managers Application - `/managers/`
Managers, request types, requests, request responses, announcements.

#### Models - `/managers/models.py`
* `Manager` - Model for a manager in a house.
* `RequestType` - Model to specify relevant managers to requests and to group requests.
* `Request` - Model for requests to managers.
* `Response` - Model for responses to requests.
* `Announcement` - Model for a manager's announcement to all members.

#### Forms - `/managers/forms.py`
* `ManagerForm` - From to create or modify a Manager.
* `RequestTypeForm` - Form to create or modify a RequestType.
* `RequestForm` - Form to create a new Request.
* `ResponseForm` - Form to create or modify a Response.
* `ManagerResponseForm` - Form for a Manager relevant to a Request to create or modify a Response.
* `VoteForm` - Form for a user to up vote a Request.
* `AnnouncementForm` - Form for a Manager to post an Announcement.
* `UnpinForm` - Form for a manager or admin to pin or unpin an Announcement to/from the homepage
and the manager announcements page.

#### Views - `/managers/views.py`
* `anonymous_login_view` - View for an admin to start an anonymous session.
* `end_anonymous_session_view` - View for an admin to end an anonymous session.
* `list_managers_view` - View of the manager directory.
* `manager_view` - View of a manager's details.
* `meta_manager_view` - View for a president or admin to manage all managers.
* `add_manager_view` - View for a president or admin to add a new manager.
* `edit_manager_view` - View for a president or admin to modify an existing manager.
* `manage_request_types_view` - View for a president or admin to manage request types.
* `add_request_type_view` - View for a president or admin to add a new request type.
* `edit_request_type_view` - View for a president or admin to edit an existing request type.
* `requests_view` - View of a request page for a given request type.
* `my_requests_view` - View for a user to see all of her/his requests in expanded form.
* `list_my_requests_view` - List view for a user's own requests.
* `list_user_requests_view` - List view of another user's requests.
* `all_requests_view` - List view of all request types and links to see all requests of each type.
* `list_all_requests_view` - View of all requests of a given type.
* `request_view` - View of an individual request.
* `announcement_view` - View of an individual announcement.
* `edit_announcement_view` - View to edit an announcement.
* `announcements_view` - View of recent and pinned announcements.
* `all_announcements_view` - View of all announcements.

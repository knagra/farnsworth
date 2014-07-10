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

### Base Application - `/base/`
Models:
* `UserProfile` - A user's profile, contains extra data: phone number, visiblity settings, etc.
* `ProfileRequest` - Model for a request for a profile on the site.

Forms:
* `ProfileRequestForm` - Form to request a user profile on the site.
* `AddUserForm` - Form for an admin (superuser) to add a new user to the site.
* `DeleteUserForm` - Form for an admin to delete a user from the site.
* `ModifyUserForm` - Form for an admin to modify a user's profile on the site.
* `ModifyProfileRequestForm` - Form for an admin to approve or delete a request for a profile on the site.
* `UpdateProfileForm` - Form for a user to update her/his profile on the site.
* `LoginForm` - Form for a user to login to the site.

Views:
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
* `reset_pw_view' - View for a user to enter an e-mail address to reset password. URL: `/reset/`
* `reset_pw_confirm_view` - View for a user to set a new password using a token generated and e-mailed by the `reset_pw_view`. URL: `/reset/<token>/`

Etc.:
* `views.add_context` - Adds variables to be sent to templates that are recurring and required by all or most templates.
* `views._get_oauth_providers` - Grab all OAuth providers that are setup for the given installation of Farnsworth.

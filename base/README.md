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

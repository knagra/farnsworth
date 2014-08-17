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

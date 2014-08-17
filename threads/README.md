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

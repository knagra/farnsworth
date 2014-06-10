'''
Project: Farnsworth

Author: Karandeep Singh Nagra

A set of variables used elsewhere in Farnsworth.
These should be things that are rarely or never changed in an implementation of Farnsworth.
'''

# The anonymous username.
ANONYMOUS_USERNAME = "spineless"

# List of time formats accepted by event forms.
time_formats = ['%m/%d/%Y %I:%M %p', '%m/%d/%Y %I:%M:%S %p', '%Y-%m-%d %H:%M:%S']

# The e-mail subject used when sending profile request approval messages.
APPROVAL_SUBJECT = "[Farnsworth - {house}] Welcome to {house}"

# The e-mail template used when sending profile request approval messages.
# username_bit should be "the username and password you selected",
# "the username <username> and the password you selected",
# or "<OAuth_provider.title()>" depending on whether the original username provided by the user was used to
# create the new user.
APPROVAL_EMAIL = '''Dear {full_name},

Your request for an account on the house site for {house} has been approved.
You may now login at {login_url} using {username_bit}.

A profile request using this e-mail address and the name above was submitted to us on {request_date}.
If you believe this was done in error, please e-mail us at {admin_email} immediately.

Thank you,
{admin_name}
{house} Site Admin




This message was auto-generated by Farnsworth (https://www.github.com/knagra/farnsworth).'''

# The e-mail subject used when sending profile request deletion messages.
DELETION_SUBJECT = "[Farnsworth - {house}] Profile Request Deleted"

# The e-mail template used when sending profile request approval messages.
DELETION_EMAIL = '''Dear {full_name},

Your request for an account on the house site for {house} has been rejected.
All the information you have provided has been permanently deleted from our database.

If you believe this was done in error, please contact us at {admin_email}.

Thank you,
{admin_name}
{house} Site Admin




This message was auto-generated by Farnsworth (https://www.github.com/knagra/farnsworth).'''

# The e-mail subject used when sending profile request submission messages.
SUBMISSION_SUBJECT = "[Farnsworth - {house}] Profile Request Received"

# The e-mail template used when sending profile request submission messages.
SUBMISSION_EMAIL = '''Dear {full_name},

Your request for a profile on the house website for {house} has been received.
If you did not make this request or you are not {full_name}, please contact us at {admin_email} immediately.

Thank you,
{admin_name}
{house} Site Admin




This message was auto-generated by Farnsworth (https://www.github.com/knagra/farnsworth).'''

# A tuple of random substrings to show underneath the 404 title in the 404 page.
SUBTEXTS_404 = ("The number you have dialed has crashed into a planet.  Please make a note of it.",
	"Good news, everyone!  Wait, that's not good news...",
	"I could fix this, but...well, I am already in my pajamas.",
	"Aaahhh..to be young again...and also a 404 page.",
	"You take one nap in a ditch in the park, and people start declaring you this and that!",
	"Oh my, yes.",
	"Better yet, I'll build a page to replace it for you.  Some kind of gamma powered mechanical monster, with freeway on-ramps for arms and a heart as black as coal...",
	"We tore the universe a new space-hole, all right.  And now it's clenching shut.",
	"You still have your old pal Zoidberg.  YOU ALL HAVE ZOIDBERG!!!",
	"Woob woob woob woob woob!",
	"Science cannot move forward without heaps!",
	"It's nothing a lawsuit won't cure.",
	"Well, we're boned.",
	"Sweet Yeti of the Serengeti! She's gone crazy Eddie in the heady!",
	"Have you ever thought about turning off the TV, sitting down with your children, and hitting them?",
	"I'm back, baby!",
	"Let's go, alreadaaaay!",
	"Yeah, well, I'm gonna go make my own theme park.  With blackjack.  And hookers! In fact, forget the park!",
	"Fine, I'll go build my own lunar lander.  With blackjack.  And hookers!  In fact, forget the lunar lander and the blackjack!  Eeeh, screw the whole thing!",
	"Kill all humans...kill all humans...",
	"Like most of life's problems, this one can be solved by bending.",
	"Tempers are wearing thin.  Let's just hope some robot doesn't kill everybody.",
	"It worked for me.  I used to be a little blonde girl named Virginia.",
	"Maybe it's time to leave the science to the hundred and twenty year olds.",
	"Let's face it, comedy is a dead artform.  Now, tragedy...that's funny.",
	"The web page that browses back.",
	"One word: Thundercougarfalconbird.",
	"Nothing makes you feel more like a man than a Thundercougarfalconbird.",
	)

# Standard messages sent to clients on errors.
MESSAGES = {
	'ADMINS_ONLY': "You do not have permission to view the page you were trying to access.",
	'ADMIN_PASSWORD': "You are not allowed to change your own password from this page.",
	'SELF_DELETE': "You are not allowed to delete yourself.",
	'NO_PROFILE': "A profile for you could not be found.  Please contact a site admin.",
	'UNKNOWN_FORM': "Your post request could not be processed.  Please contact a site admin.",
	'MESSAGE_ERROR': "Your message post was not successful.  Please try again.",
	'THREAD_ERROR': "Your thread post was not successful.  Both subject and body are required.  Please try again.",
	'USER_ADDED': "User {username} was successfully added.",
	'USER_DELETED': "User {username} was successfully deleted.",
	'PREQ_DEL': "Profile request by {first_name} {last_name} for username {username} successfully deleted.",
	'USER_PROFILE_SAVED': "User {username}'s profile has been successfully updated.",
	'USER_PW_CHANGED': "User {username}'s password has been successfully changed.",
	'PASSWORD_UNHASHABLE': "Could not hash password.  Please try again.",
	'PROFILE_SUBMITTED': "Your request has been submitted.  An admin will contact you soon.",
	'PROFILE_TAKEN': "An account request for {first_name} {last_name} has already been made.",
	'USERNAME_TAKEN': "This username is taken.  Try one of {username}_1 through {username}_10.",
	'INVALID_LOGIN': 'Invalid username/password combination. Forgot your username/password? You can reset your password at <a href="{reset_url}">{reset_url}</a>.',
	'EMAIL_TAKEN': "This e-mail address is already taken.",
	'EMAIL_TAKEN_RESET': 'This e-mail address is already taken.  Forgot your password?  You can reset it here: <a href="{reset_url}">{reset_url}</a>.',
	'INVALID_USERNAME': 'Invalid username. Must be characters A-Z, a-z, 0-9, or _.',
	'EVENT_ERROR': "Your event post was not successful.  Please check for errors and try again.",
	'RSVP_ADD': "You've been successfully added to the list of RSVPs for {event}.",
	'RSVP_REMOVE': "You've been successfully removed from the list of RSVPs for {event}.",
	'EVENT_UPDATED': "Event {event} successfully updated.",
	'REQ_CLOSED': "Request successfully marked closed.",
	'REQ_FILLED': "Request successfully marked filled.",
	'SPINELESS': "You cannot modify the anonymous user profile.",
	'ANONYMOUS_EDIT': "THIS IS THE ANONYMOUS USER PROFILE.  IT IS HIGHLY RECOMMENDED THAT YOU NOT MODIFY IT. IT SHOULD BE INACTIVE TO PREVENT USERS FROM TRYING TO MANUALLY LOGIN AS THE ANONYMOUS USER.",
	'ANONYMOUS_DENIED': "Only superadmins are allowed to login the anonymous user or end the anonymous session.",
	'ANONYMOUS_LOGIN': "You have successfully logged out and started an anonymous session on this machine.",
	'ANONYMOUS_SESSION_ENDED': "You have successfully ended the anonymous session on this machine.",
	'RECOUNTED': "Thread messages and request responses successfully recounted.  {threads_changed} of {thread_count} threads and {requests_changed} of {request_count} requests were out-of-date and updated.",
	'ALREADY_PAST': "This event has already passed.  You can no longer RSVP to this event.",
	'LAST_SUPERADMIN': "You are the only superadmin in the database.  To prevent permanent system lock-out, you have been prevented from changing your own superadmin status.",
	'PRESIDENTS_ONLY': "This page is restricted to Presidents and superadmins.",
	'WORKSHIFT_MANAGER_ONLY': "This page is restricted to Workshift Managers and superadmins.",
	'NO_MANAGER': "The manager page {managerTitle} could not be found.",
	'NO_REQUEST_TYPE': "The request type {requestType} could not be found.",
	'MANAGER_ADDED': "Manager {managerTitle} has been successfully added.",
	'MANAGER_SAVED': "Manager {managerTitle} has been successfully saved.",
	'INVALID_FORM': "Your input could not be properly processed.  Please try again.",
	'INACTIVE_MANAGER': "{managerTitle} is currently deactivated.",
	'REQUEST_TYPE_ADDED': "Request type {typeName} has been successfully added.",
	'REQUEST_TYPE_SAVED': "Request type {typeName} has been successfully saved.",
	'PROFILE_REQUEST_APPROVAL_EMAIL': ' A profile request approval e-mail was successfully sent to {full_name} at <a title="Write E-mail" href="mailto:{email}">{email}</a>.', # The initial space is necessary.
	'PROFILE_REQUEST_DELETION_EMAIL': ' A profile request deletion e-mail was successfully sent to {full_name} at <a title="Write E-mail" href="mailto:{email}">{email}</a>.', # The initial space is necessary.
	'EMAIL_FAIL': ' Farnsworth failed at sending an e-mail to <a title="Write E-mail" href="mailto:{email}">{email}</a>.', # Initial space necessary.
}

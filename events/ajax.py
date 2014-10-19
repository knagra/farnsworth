"""
Project: Farnsworth

Authors: Karandeep Singh Nagra and Nader Morshed

AJAX utilities for the events package.
"""

from django.core.urlresolvers import reverse


def build_ajax_rsvps(event, user_profile):
    """Return link and list strings for a given event."""
    if user_profile in event.rsvps.all():
        link_string = True
    else:
        link_string = False

    if not event.rsvps.all().count():
        list_string = 'No RSVPs.'
    else:
        list_string = 'RSVPs:'
        for counter, profile in enumerate(event.rsvps.all()):
            if counter > 0:
                list_string += ','

            list_string += \
                ' <a class="page_link" title="View Profile" href="{url}">' \
                    '{name}</a>'.format(
                        url=reverse(
                            'member_profile',
                            kwargs={'targetUsername': profile.user.username}
                        ),
                        name='You' if profile.user == user_profile.user \
                            else profile.user.get_full_name(),
                    )
    return (link_string, list_string)
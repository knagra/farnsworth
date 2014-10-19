"""
Project: Farnsworth

Authors: Karandeep Singh Nagra and Nader Morshed


AJAX utilities for the managers module.
"""

from django.core.urlresolvers import reverse


def build_ajax_votes(request, user_profile):
    """Build vote information for the request."""
    vote_list = ''
    for profile in request.upvotes.all():
        vote_list += \
            '<li><a title="View Profile" href="{url}">{name}</a></li>'.format(
                url=reverse(
                    'member_profile',
                    kwargs={'targetUsername': profile.user.username}
                ),
                name='You' if profile.user == user_profile.user \
                    else profile.user.get_full_name(),
            )

    in_votes = user_profile in request.upvotes.all()
    count = request.upvotes.all().count()

    return (vote_list, in_votes, count)

"""
Project: Farnsworth

Authors: Karandeep Singh Nagra and Nader Morshed
"""

from datetime import timedelta

from django.utils.timezone import now

from django_cron import CronJobBase, Schedule

from farnsworth.settings import REQUEST_EXPIRATION_HOURS
from managers.models import Request, Response


class ExpireRequestsCronJob(CronJobBase):
    """
    Expire OPEN requests that are more than REQUEST_EXPIRATION_HOURS old
    and have no REOPENED responses and no responses within the past
    REQUEST_EXPIRATION_HOURS associated with them.
    REOPENED responses are omitted to allow managers to reopen expired requests
    and not have those requests automatically expired by the system again.
    Responses within the past REQUEST_EXPIRATION_HOURS exclude expiration
    as such responses demontrate ongoing value or interest.
    """
    RUN_AT_TIMES = ['00:01',]
    RUN_EVERY_MINS = 60

    schedule = Schedule(run_at_times=RUN_AT_TIMES, run_every_mins=RUN_EVERY_MINS)
    code = 'managers.expire_requests'

    def do(self):
        cutoff = now() - timedelta(hours=REQUEST_EXPIRATION_HOURS)
        for req in Request.objects.filter(status=Request.OPEN, post_date__lte=cutoff):
            # Don't re-close a request that was already re-opened at least once
            if req.response_set.filter(action=Response.REOPENED).count():
                continue
            # Skip requests with replies after the cutoff period
            if req.response_set.filter(post_date__lte=cutoff).count():
                continue
            req.status = Request.EXPIRED
            req.save()

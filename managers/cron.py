"""
Project: Farnsworth

Authors: Karandeep Singh Nagra and Nader Morshed
"""

from datetime import timedelta

from django.utils.timezone import now

from django_cron import CronJobBase, Schedule

from farnsworth.settings import REQUEST_EXPIRATION_HOURS
from managers.models import Request


class ExpireRequests(CronJobBase):
    RUN_AT_TIMES = ['00:01',]
    RUN_EVERY_MINS = 60

    schedule = Schedule(run_at_times=RUN_AT_TIMES, run_every_mins=RUN_EVERY_MINS)
    code = 'managers.expire_requests'

    def do(self):
        for req in Request.objects.filter(post_date__lte=now()-timedelta(hours=REQUEST_EXPIRATION_HOURS)):
            req.status = Request.EXPIRED
            req.save()

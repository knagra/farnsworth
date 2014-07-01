
from django_cron import CronJobBase, Schedule

from workshift import utils

class CollectBlownCronJob(CronJobBase):
	RUN_EVERY_MINS = 15

	schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
	code = "workshift.collect_blown"

	def do(self):
		utils.collect_blown()

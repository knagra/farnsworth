
import sys

from django.conf import settings

from utils.funcs import convert_to_url
from managers.models import Manager, RequestType

def _main(args):
	# Add Managers
	managers = [
		("President", "5 hours/week", "", "hp"),
		("Vice President", "3 hours/week", "", ""),
		("Board Representative", "5 hours/week", "", "br"),
		("House Manager", "5 hours/week + 56.25% rent compensation", "", "hm"),
		("Finance Manager", "5 hours/week", "", ""),
		("Kitchen Manager", "5 hours/week + 100% rent compensation", "", "km"),
		("IKC Manager", "5 hours/week", "", ""),
		("Workshift Manager", "5 hours/week + 56.25% rent compensation", "", "wm"),
		("Maintenance Manager", "5 hours/week + 43.75% rent compensation", "", "mm"),
		("Social Manager", "5 hours/week", "", "sm"),
		("Network Manager", "3 hours/week", "", "nm"),
		("Garden Manager", "3 hours/week", "", ""),
		("Waste Reduction Manager", "5 hours/week", "", "rm"),
		("Health Worker", "2 hours/week", "", "hw"),
		]
	for title, compensation, duties, email in managers:
		m = Manager(
			title=title,
			url_title=convert_to_url(title),
			compensation=compensation,
			duties=duties,
			email="{0}{1}@bsc.coop".format(settings.HOUSE_SHORT, email) if email else "",
			president="president" in title.lower(),
			workshift_manager="workshift" in title.lower(),
			)
		m.save()

	# Add Requests
	requests = [
		("Cleanliness", ["IKC Manager", "Workshift Manager"], "certificate"),
		("Finance", ["Finance Manager"], "usd"),
		("Food", ["Kitchen Manager"], "cutlery"),
		("Health", ["Health Worker"], "heart"),
		("House", ["House Manager"], "home"),
		("Maintenance", ["Maintenance Manager"], "wrench"),
		("Network", ["Network Manager"], "signal"),
		("President", ["President"], "star"),
		("Social", ["Social Manager"], "comment"),
		]
	for name, managers, glyphicon in requests:
		r = RequestType(
			name=name,
			url_name=convert_to_url(name),
			glyphicon=glyphicon,
			)
		r.save()
		r.managers = [Manager.objects.get(title=i) for i in managers]
		r.save()

	# Add Workshifts
	# ...

if __name__ == "__main__":
	_main(sys.argv[1:])

#!/bin/sh
set -e

for i in farnsworth afro hoyt
do
	cd ../$i
	git pull
	./manage.py collectstatic
	./manage.py test
done


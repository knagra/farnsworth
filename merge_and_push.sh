#!/bin/sh
set -e

for i in kingman afro hoyt
do
	git checkout $i
	git pull
	git merge master
	git push
done


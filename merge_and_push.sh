#!/bin/sh
set -e

git checkout master
git pull
git push

for i in kingman afro hoyt
do
	git checkout $i
	git pull
	git merge master
	git push
done

git checkout master

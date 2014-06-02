#!/bin/sh
set -e

git checkout master
git pull
git push

for i in $(git branch --list | grep -v master)
do
	git checkout $i
	git pull origin $i
	git merge master
	git push origin $i
done

git checkout master

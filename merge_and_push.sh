#!/bin/sh
set -e

git checkout master
git pull
git push

for i in $(git branch --list | grep -v master)
do
	git checkout $i
	git pull
	git merge master
	git push
done

git checkout master

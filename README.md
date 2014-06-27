# Farnsworth

[![Coverage Status](https://coveralls.io/repos/knagra/farnsworth/badge.svg?branch=master)](https://coveralls.io/r/knagra/farnsworth?branch=master)
[![Build Status](https://travis-ci.org/knagra/farnsworth.svg?branch=master)](https://travis-ci.org/knagra/farnsworth)

## Authors

* Karandeep Singh Nagra
* Nader Morshed

## Description

An online gathering place for each house in the BSC.  Scalable and modular, intended to be used as an instance at each house.

No authorship claim is made to the contents of the subdirectories tinymce, jquery, and bootstrap of directory static, with the exception of the file static/tinymce/layout.js.  Please consult the relevant licenses before distributing or using those portions of this software.

Logos included in the /static/ui/images/oauth are property and copyright of the
respective companies.

Built with Django, Python, and SQLite. Tested and deployed on PostgreSQL.

Live versions of the site can be accessed at https://kingmanhall.org/internal/, https://kingmanhall.org/afro/, and https://kingmanhall.org/hoyt/.

## Dependencies

* Django >= 1.6
* Python >= 2.6
* SQLite3 (for running tests)
* TinyMCE 4.0.21 (included in static folder)
* jQuery 1.11.0 (included in static/jquery folder)
* tablesorter 2.15.13 (included in static/jquery folder)
* Nivo Slider 3.2 (included in static/jquery folder)
* Bootstrap 3.1.1
* django-bootstrap-form 3.1
* moment.js (included in static folder)
* bootstrap-datetime-picker (included in static/bootstrap/js and static/ui/css)
* Django-Haystack 2.1.1-dev (from GitHub, read 'Get started' on haystacksearch.org)
* elasticsearch 1.2.1 (https://www.elasticsearch.org/overview/elkdownloads/)
* Python elasticsearch
* Python Social Auth 0.1.23

## Installation
### CentOS

To install all of the dependencies of CentOS, run the following as root:

```
# yum install postgres python python-devel virtualenv gcc mod_wsgi
```

### Debian

To install all of the dependencies of Debian, run the following as root:

```
# apt-get install postgresql python python-dev python-virtualenv gcc libapache2-mod-wsgi libpq-dev sqlite3
```

See http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/setup-repositories.html on installing elasticsearch on either distribution.

### virtualenv

Once your system packages have been installed, run the following as the apache user to set up a virtual environment with the site-specific packages

```
$ cd /path/to/farnsworth
$ virtualenv .
$ source bin/activate
$ pip install -r requirements.txt
```

### Apache

Add the following lines to the httpd.conf file for Apache:

```
WSGIPythonPath /path/to/farnsworth/lib/python<python-version>/site-packages

...

<VirtualHost domainname.com:80>
    ...

    WSGIScriptAlias /farnsworth /path/to/farnsworth/farnsworth/wsgi.py

    Alias /static/ /path/to/farnsworth/static/
</VirtualHost>
```

### PostgreSQL

To create the PostgreSQL database, enter the following as root:

```
# su - postgres
$ createdb <house>
$ createuser -PS <house>_admin
$ psql
postgres=# GRANT ALL PRIVILEGES ON DATABASE <house> TO <house>_admin;
```

### SELinux

To enable the use of PostgreSQL and elasticsearch, enter the following as root:

```
# setsebool -P httpd_can_network_connect_db 1
# setsebool -P httpd_can_network_connect on
```

### Backups
#### SQLite

Simply copy and compress the SQLite database file:

```
$ gzip farnsworth/<house>.db > "backup-<house>-$(date +%F).db.gz"
```

And restore by decompressing and copying back:

```
$ gunzip backup-<house>-<date>.db.gz > farnsworth/<house>.db
```

### PostgreSQL

Back up the house's database with the following command:

```
$ pg_dump -U <house>_admin <house> | gzip > "backup-<house>-$(date +%F).db.gz"
```

Restore the house's database with the following command:

```
$ gunzip -c backup-<house>-<date>.db.gz | psql -U <house>_admin <house>
```

See http://www.postgresql.org/docs/current/static/backup.html for a detailed description of other methods to back up the database.

[![Coverage Status](https://coveralls.io/repos/knagra/farnsworth/badge.svg?branch=master)](https://coveralls.io/r/knagra/farnsworth?branch=master)
[![Build Status](https://travis-ci.org/knagra/farnsworth.svg?branch=master)](https://travis-ci.org/knagra/farnsworth)

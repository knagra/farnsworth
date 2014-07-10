# Farnsworth

[![Coverage Status](https://coveralls.io/repos/knagra/farnsworth/badge.png?branch=master)](https://coveralls.io/r/knagra/farnsworth?branch=master)
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

## Logical Structure
Check `/DOCS/README.md` (<a href="https://github.com/knagra/farnsworth/blob/master/DOCS/README.md">here</a>)
for complete details on the logical structure of the application, where to begin when
first introducing yourself to Farnsworth, and how to develop the site further.

## Installation
### CentOS

To install all of the dependencies of CentOS, run the following as root:

```
# yum install postgres python python-devel virtualenv gcc mod_wsgi mercurial git
```

#### SELinux

CentOS comes pre-packaged with SELinux for increased security. To enable the use of PostgreSQL and elasticsearch in this context, run the following as root:

```
# setsebool -P httpd_can_network_connect_db 1
# setsebool -P httpd_can_network_connect on
```

### Debian

To install all of the dependencies of Debian, run the following as root:

```
# apt-get install postgresql python python-dev python-virtualenv gcc libapache2-mod-wsgi libpq-dev sqlite3 mercurial git
```

### elasticsearch

See http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/setup-repositories.html on installing elasticsearch on either distribution.

### virtualenv

Once your system packages have been installed, run the following as the apache user or root to set up a virtual environment with the site-specific packages:

```
$ cd /path/to/farnsworth
$ virtualenv .
$ source bin/activate
$ pip install -r requirements.txt
```

### Configuration

In order to configure your personal Farnsworth, you will need to configure its settings. A brief list of house-specific settings is read from `farnsworth/house_settings.py`:

```
$ cd /path/to/farnsworth
$ cp farnsworth/house_settings.py.example farnsworth/house_settings.py
$ $EDITOR farnsworth/house_settings.py
```

See `farnsworth/settings.py` for the full list of settings used by Django.

### HTTP Proxy

Though you can run django applications with ./manage.py runserver, it is usually preferable to place them behind a HTTP proxy. This allows you to add HTTPS for encryption and host other applications or static pages on the same domain. Popular proxies include Apache, nginx, and unicorn.

#### Apache

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

### Database
#### SQLite

Farnsworth is set up to use SQLite by default. The database will be stored in farnsworth/farnsworth.db

#### PostgreSQL

To create the PostgreSQL database, run the following commands as root:

```
# su - postgres
$ createdb <house>
$ createuser -PS <house>_admin
Enter password for new role:
Enter it again:
Shall the new role be able to create databases? (y/n) n
Shall the new role be allowed to create more new roles? (y/n) n
$ psql
postgres=# GRANT ALL PRIVILEGES ON DATABASE <house> TO <house>_admin;
GRANT
postgres=# \q
```

Make sure to update farnsworth/house_settings.py with the password for the postgres user.

#### Initialization

To create the tables in the database and an initial user, first start elasticsearch as root:

```
# service elasticsearch start
```

Then run the following as a user with write access to the farnsworth directory:

```
$ cd /path/to/farnsworth
$ source bin/activate
$ ./manage.py syncdb
$ ./manage.py collectstatic
```

There will be a prompt to create a superuser, if you mistakenly close the prompt before the user is created, you can get back to it with: `./manage.py createsuperuser`

Once you have the site up and running, navigate to /admin/sites/site/ and update the example.com site to have your domain.  Django grabs this domain when sending e-mails, etc. to create links to your site.

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

#### PostgreSQL

Back up the house's database with the following command:

```
$ pg_dump -U <house>_admin <house> | gzip > "backup-<house>-$(date +%F).db.gz"
```

Restore the house's database with the following command:

```
$ gunzip -c backup-<house>-<date>.db.gz | psql -U <house>_admin <house>
```

See http://www.postgresql.org/docs/current/static/backup.html for a detailed description of other methods to back up the database.

[![Coverage Status](https://coveralls.io/repos/knagra/farnsworth/badge.png?branch=master)](https://coveralls.io/r/knagra/farnsworth?branch=master)
[![Build Status](https://travis-ci.org/knagra/farnsworth.svg?branch=master)](https://travis-ci.org/knagra/farnsworth)

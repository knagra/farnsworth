# Farnsworth

[![Build Status][build]](https://travis-ci.org/knagra/farnsworth)[![Coverage Status][cover]](https://coveralls.io/r/knagra/farnsworth?branch=master)

[build]: https://img.shields.io/travis/knagra/farnsworth/master.svg?style=flat-square
[cover]: http://img.shields.io/coveralls/knagra/farnsworth/master.svg?style=flat-square

## Authors

* Karandeep Singh Nagra
* Nader Morshed

## Description

An online gathering place for each house in the BSC.  Scalable and modular,
intended to be used as an instance at each house.

No authorship claim is made to the contents of the subdirectories ckeditor,
tinymce, jquery, jquery-ui, and bootstrap of directory /base/static, with the
exception of the file /base/static/ckeditor/config.js.  Please consult the
relevant licenses before distributing or using those portions of this
software.

Logos included in the /static/ui/images/oauth are property and copyright of the
respective companies.

Built with Django and Python.

A live version of the site can be accessed at https://kingmanhall.org/.

## Logical Structure

Check `/DOCS/README.md` (<a href="https://github.com/knagra/farnsworth/blob/master/DOCS/README.md">here</a>)
for complete details on the logical structure of the application, where to
begin when first introducing yourself to Farnsworth, and how to develop the
site further.

## Deployment

The primary method of deployment of Farnsworth is using Docker. See
[docker-farnsworth](https://github.com/naderm/docker-farnsworth) for more
information.

## Development
### CentOS

To install all of the dependencies of CentOS for development, run the following
as root:

```
# yum install epel-release
# yum install python python-devel python-virtualenv gcc mod_wsgi git libffi-devel postgresql-devel
```

### Debian

To install all of the dependencies of Debian, run the following as root:

```
# apt-get install python python-dev python-virtualenv gcc libapache2-mod-wsgi libpq-dev sqlite3 git libffi-dev
```

### virtualenv

Once your system packages have been installed, run the following as your user
to install the required python packages:

```
$ cd /path/to/farnsworth
$ virtualenv .
$ source bin/activate
$ pip install -r requirements.txt
```

### Configuration

In order to configure your personal Farnsworth, you will need to configure its
settings. A brief list of house-specific settings is read from
`farnsworth/house_settings.py`:

```
$ cd /path/to/farnsworth
$ cp farnsworth/house_settings.py.example farnsworth/house_settings.py
$ $EDITOR farnsworth/house_settings.py
```

See `farnsworth/settings.py` for the full list of settings used by Django.

#### Initialization

To create the tables in the database and an initial user:

```
$ cd /path/to/farnsworth
$ source bin/activate
$ ./manage.py collectstatic
$ ./manage.py migrate
```

There will be a prompt to create a superuser, if you mistakenly close the
prompt before the user is created, you can get back to it with: `./manage.py
createsuperuser`.

Once you have the site up and running, navigate to /admin/sites/site/ and
update the example.com site to have your domain.  Django grabs this domain when
sending e-mails, etc. to create links to your site.

### Testing

Once the dependencies have been installed and the database initialized, you can
start your own development instance by running:

```
$ ./manage.py runserver
```

Then navigate to `http://localhost:8000/` to view the website.

### Scheduler

In order for the workshift application to regularly mark shifts as blown, you
will need to add a cron job to execute an internal scheduler every five
minutes. Here, <username> can be the apache / httpd user or another user that
has access to the installation:

```
crontab -u <username> -e
# Append the following line:
*/5 * * * * source /path/to/farnsworth/bin/activate && /path/to/farnsworth/manage.py runcrons
```

Alternatively, create the following file:

```
# cat > /etc/cron.d/farnsworth <<< "*/5 * * * * <username> source /path/to/farnsworth/bin/activate && /path/to/farnsworth/manage.py runcrons"
```

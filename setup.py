
from __future__ import print_function

import os
from setuptools import setup, find_packages

os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

required = [
    line.strip()
    for line in open("requirements.txt").read().split("\n")
    if line.strip()
]

setup(
    name="Farnsworth",
    version="2.3.3",
    author="Karandeep Nagra",
    url="https://github.com/knagra/farnsworth",
    author_email="karandeepsnagra@gmail.com",
    packages=find_packages(),
    include_package_data=True,
    description="Website for BSC houses.",
    install_requires=required +  ["elasticsearch==1.0.0"],
    tests_require=required,
    test_suite="runtests.runtests",
    package_data={
        "": ["*/static/*/*/*", "*/templates/*", "templates/search/*/*/*"],
    },
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Django",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        # "Programming Language :: Python :: 3.3",
        # "Programming Language :: Python :: 3.4",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
    dependency_links=[
        "git://github.com/naderm/django-phonenumber-field.git#egg=django_phonenumber_field-develop",
        "git://github.com/naderm/django-notifications.git#egg=django_notifications-master",
    ],
    extras_require={
        "PostgreSQL": ["psycopg2"],
        "social-auth": ["python-social-auth"],
    },
)

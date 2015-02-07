
from __future__ import print_function

import re
import os
from setuptools import setup, find_packages

os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

def _required_to_setup(required):
    install_requires, dependency_links = [], []
    for package in required:
        m = re.match("(.*)://(.*)/(.*)(\.git)?#egg=(.*)", package)

        if not m:
            install_requires.append(package)
        else:
            install_requires.append(m.group(3))
            dependency_links.append(package)

    return install_requires, dependency_links

install_required, dependency_links = _required_to_setup([
    line.strip()
    for line in open("requirements.txt").read().split("\n")
    if line.strip()
])

setup(
    name="Farnsworth",
    version="2.3.3",
    author="Karandeep Nagra",
    url="https://github.com/knagra/farnsworth",
    author_email="karandeepsnagra@gmail.com",
    packages=find_packages(),
    include_package_data=True,
    description="Website for BSC houses.",
    install_requires=install_required,
    tests_require=install_required,
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
    dependency_links=dependency_links,
    extras_require={
        "PostgreSQL": ["psycopg2"],
        "social-auth": ["python-social-auth"],
    },
)

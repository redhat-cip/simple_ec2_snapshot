#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from simplec2snap import __version__

setup(
    name='simplec2snap',
    version=__version__,
    packages=find_packages(),
    author="Pierre Mavro",
    author_email="deimos@deimos.fr",
    description="Simple solution to backup ec2 instances using snapshots",
    long_description=open('README.md').read(),
    install_requires=open('requirements.txt').read().splitlines(),
    include_package_data=True,
    url='https://github.com/enovance/simple_ec2_snapshot',
    classifiers=[
        "Programming Language :: Python",
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)",
        "Environment :: Console",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.7",
        "Topic :: Communications",
    ],
)

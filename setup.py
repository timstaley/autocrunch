#!/usr/bin/env python

from setuptools import setup

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name="autocrunch",
    version="0.1",
    packages=['autocrunch'],
    description="Example of using pyinotify to automatically process incoming files.",
    author="Tim Staley",
    author_email="timstaley337@gmail.com",
    url="https://github.com/timstaley/autocrunch",
    install_requires=required,
)

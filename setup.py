#!/usr/bin/env python

# Copyright Claudio Mattera 2019.
# Copyright Center for Energy Informatics 2018.
# Distributed under the MIT License.
# See accompanying file License.txt, or online at
# https://opensource.org/licenses/MIT

import sys

from setuptools import setup

setup(
    name="temperature-ds18s20-stanley-driver",
    version="0.1.2",
    description="Records Linux load information to a Stanley database",
    long_description=open("Readme.md").read(),
    author="Claudio Giovanni Mattera",
    author_email="claudio@mattera.it",
    url="https://gitlab.com/claudiomattera/temperature-ds18s20-stanley-driver/",
    license="MIT",
    packages=[
        "temperature_ds18s20_stanley_driver",
    ],
    include_package_data=True,
    entry_points={
        "gui_scripts": [
            "temperature-ds18s20-stanley-driver = temperature_ds18s20_stanley_driver.__main__:main",
        ],
    },
    install_requires=[
        "pystanley",
        "pandas",
        "tzlocal",
    ],
)

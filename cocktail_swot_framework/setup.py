#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
#  setup.py
#  
#  Copyright 2018 Francesco Antoniazzi <francesco.antoniazzi@unibo.it>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  

import setuptools
import yaml

setuptools.setup(
    name="cocktail",
    version="1",
    author="Francesco Antoniazzi",
    author_email="francesco.antoniazzi@unibo.it",
    description="Cocktail package",
    url="https://github.com/fr4ncidir/SemanticWoT.git",
    packages=setuptools.find_packages(),
    license="GNU GPL3",
    test_suite="cocktail.tests",
    classifiers=(
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ),
    install_requires=[
        "sepy", "jinja2", "rdflib", "rdflib-jsonld", "pyld"
    ],
    dependency_links=[
        "git+https://github.com/arces-wot/SEPA-python3-APIs.git"
    ],
    include_package_data=True
)

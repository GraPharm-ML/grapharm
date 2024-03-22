#!/usr/bin/env python

"""
Setup module for GraPharm
"""

import os
import sys

from setuptools import setup, find_packages

sys.path.insert(0, f"{os.path.dirname(__file__)}/grapharm")

import grapharm

project_root = os.path.join(os.path.realpath(os.path.dirname(__file__)), "grapharm")

setup(
    name="grapharm",
    entry_points={
        "console_scripts": [
            "grapharm = grapharm.__main__:main",
        ],
    },
    package_data={"": ["edge_colors.json"]},
    packages=find_packages(),
    version=grapharm.__version__,
    install_requires=[
        "scipy",
        "numpy",
        "pandas",
        "selenium",
        "beautifulsoup4",
        "matplotlib",
        "pyvis",
        "pygraphviz",
        "jupyter",
        "networkx",
        "ipykernel",
        "easydict"
    ],
)
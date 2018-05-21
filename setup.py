#!/usr/bin/env python3

from setuptools import setup, find_packages

setup(
    name='librus',
    description="Librus Synergia API",
    version='0.0.6',
    packages=find_packages(),
    setup_requires=[
        # 'pytest-runner==3.0',
    ],
    install_requires=[
        'requests-html',
    ],
    tests_require=[
        # 'pytest==3.3.1',
    ],
    zip_safe=True,  # just to silence setuptools
)

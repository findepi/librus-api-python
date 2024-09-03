#!/usr/bin/env python3

from setuptools import setup, find_packages

setup(
    name='librus',
    description="Librus Synergia API",
    url="https://github.com/findepi/librus-api-python",
    version='0.0.15',
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
    python_requires='>=3',
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: Apache Software License",
    ],
)

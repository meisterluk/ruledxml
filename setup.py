#!/usr/bin/env python

"""
    ruledxml
    ~~~~~~~~

    Rule-based XML transformations.
    To install *ruledxml* use pip3:

    .. code:: bash
        $ pip3 install ruledxml

    (C) 2015, meisterluk, BSD 3-clause license
"""

import os.path

from setuptools import setup


def readfile(fname):
    with open(os.path.join(os.path.dirname(__file__), fname)) as fp:
        return fp.read()

setup(
    name='ruledxml',
    version='1.6.0',
    url='http://lukas-prokop.at/proj/ruledxml/',
    license='BSD',
    author='Lukas Prokop',
    author_email='admin@lukas-prokop.at',
    description='Rule-based XML transformations',
    long_description=readfile('README.rst'),
    packages=['ruledxml'],
    platforms='any',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Financial and Insurance Industry',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.5',
        'Topic :: Office/Business',
        'Topic :: Text Processing :: Markup :: XML'
    ],
    requires=['lxml (==3.4.4)'],
    scripts=['bin/ruledxml', 'bin/ruledxml-batched']
)

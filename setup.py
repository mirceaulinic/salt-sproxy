#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
The setup script for Salt SProxy
'''
import codecs
from setuptools import setup, find_packages

__author__ = 'Mircea Ulinic <ping@mirceaulinic.net>'

with codecs.open('pypi.rst', 'r', encoding='utf8') as file:
    long_description = file.read()

with open("requirements.txt", "r") as fs:
    reqs = [r for r in fs.read().splitlines() if (len(r) > 0 and not r.startswith("#"))]

setup(
    name='salt-sproxy',
    version='2019.6.0',
    namespace_packages=['salt_sproxy'],
    packages=find_packages(),
    author='Mircea Ulinic',
    author_email='ping@mirceaulinic.net',
    description='Salt plugin for interacting with network devices, without running Minions',
    long_description=long_description,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'License :: OSI Approved :: Apache Software License',
        'Topic :: Utilities',
        'Topic :: System :: Networking',
        'Topic :: System :: Clustering',
        'Topic :: System :: Operating System',
        'Topic :: System :: Distributed Computing',
        'Topic :: System :: Systems Administration',
        'Programming Language :: Python',
        'Programming Language :: Cython',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: MacOS',
        'Intended Audience :: Developers',
        'Intended Audience :: Telecommunications Industry',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
    ],
    url='https://github.com/mirceaulinic/salt-sproxy',
    license="Apache License 2.0",
    keywords=('salt', 'network', 'automation', 'cli', 'proxy', 'minion'),
    include_package_data=True,
    install_requires=reqs,
    entry_points={'console_scripts': ['salt-sproxy=salt_sproxy.scripts:salt_sproxy']},
    data_files=[('man/man1', ['docs/man/salt-sproxy.1'])],
)

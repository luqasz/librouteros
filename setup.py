#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# dirty hack http://bugs.python.org/issue8876
import os
del os.link

from distutils.core import setup

from versioning import on_master, get_branches, get_version, stable_version
from librouteros import __version__ as pkg_version

branches = get_branches()
version = get_version()
on_master = on_master( branches )

print('current version is: ', version)

if pkg_version != version:
    exit('version from package differs from GIT tag !')

if ( on_master and not stable_version(version)):
    exit('can not do anything on non-stable release. Fix git tag !')

setup(name='librouteros',
    version=version(),
    description='Python3 implementation of RouterOS API',
    author='Łukasz Kostka',
    author_email='ukasz83@gmail.com',
    url='https://github.com/uqasz/librouteros',
    packages=['librouteros'],
    license='GNU GPLv3',
    keywords='mikrotik routeros api',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: MacOS',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Operating System :: Unix',
        'Programming Language :: Python :: 3.2',
        'Topic :: Software Development :: Libraries'
        ]
     )

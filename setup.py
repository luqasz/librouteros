# -*- coding: UTF-8 -*-

import os
from setuptools import setup
from sys import version_info

here = os.path.dirname(__file__)


def read(fname):
    """
    Read given file's content.
    :param str fname: file name
    :returns: file contents
    :rtype: str
    """
    return open(os.path.join(here, fname)).read()


if version_info.major >= 3:
    install_pkgs = ()
else:
    install_pkgs = (
            'chainmap'
            )

tests_pkgs = (
        'pytest-xdist==1.*',
        'pytest==3.*',      # pytest 3.x does not work on python 3.2
        'pylama',
        'pydocstyle',
        'mock',
        )

setup_pkgs = (
        'setuptools>=12.0.5',
        )

dev_pkgs = (
        'bumpversion',
        )

setup(
    install_requires=install_pkgs,
    tests_require=tests_pkgs,
    setup_requires=setup_pkgs,
    extras_require={
        'tests': tests_pkgs,
        'develop': dev_pkgs,
    },
    zip_safe=False,
    name='librouteros',
    version='2.1.0',
    description='Python implementation of MikroTik RouterOS API',
    long_description=read('README.rst'),
    author='Łukasz Kostka',
    author_email='lukasz.kostka@netng.pl',
    url='https://github.com/luqasz/librouteros',
    packages=['librouteros'],
    license='GNU GPLv2',
    keywords='mikrotik routeros api',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Operating System :: MacOS',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Operating System :: Unix',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Software Development :: Libraries'
        ]
     )

# -*- coding: UTF-8 -*-

import os
from setuptools import setup

here = os.path.dirname(__file__)


def read(fname):
    """
    Read given file's content.
    :param str fname: file name
    :returns: file contents
    :rtype: str
    """
    return open(os.path.join(here, fname)).read()


install_pkgs = (
        )

setup_pkgs = (
        'setuptools>=12.0.5',
        )

setup(
    install_requires=install_pkgs,
    setup_requires=setup_pkgs,
    zip_safe=False,
    name='librouteros',
    version='3.2.1',
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
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Software Development :: Libraries'
        ]
     )

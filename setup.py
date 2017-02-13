# -*- coding: UTF-8 -*-

from setuptools import setup
from sys import version_info

pyversion = version_info.major, version_info.minor

if pyversion > (3, 2):
    install_pkgs = ()
else:
    install_pkgs = (
            'chainmap'
            )

tests_pkgs = (
        'pytest-xdist',
        'pytest==3.0.6',     # pytest 3.x does not work on python 3.2
        'pylama',
        'mock',
        )

dev_pkgs = (
        'bumpversion',
        )

setup(
    install_requires=install_pkgs,
    tests_require=tests_pkgs,
    extras_require={
        'tests': tests_pkgs,
        'develop': dev_pkgs,
    },
    zip_safe=False,
    name='librouteros',
    version='1.0.1',
    description='Python implementation of MikroTik RouterOS API',
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
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Libraries'
        ]
     )

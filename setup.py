#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from distutils.core import setup

setup(
	name = 'rosapi',
	version = '1.0',
	packages = ['rosapi'],
	description = 'Python3 implementation of routeros (aka mikrotik) api.',
	author = 'Łukasz Kostka',
	author_email = 'ukasz83@gmail.com',
	keywords = ['api', 'mikrotik', 'routeros', 'management'],
	url = 'http://xio.com.pl/redmine/projects/rosapi',
	download_url = 'http://xio.com.pl/redmine/projects/rosapi/files',
	license = 'GNU GENERAL PUBLIC LICENSE v3',
	long_description = open('README.md').read(),
)

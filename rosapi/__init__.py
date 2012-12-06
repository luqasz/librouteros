# -*- coding: UTF-8 -*-

# This library is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from binascii import unhexlify, hexlify
from hashlib import md5
import socket

import rosapi._rosapi
from rosapi._exceptions import *

def login(address, username, password, port=8728):
	"""
	login to RouterOS via api
	takes:
		(string) address = may be fqdn or ip/ipv6 address
		(string) username = username to login
		(string) password = password to login
		(int) port = port to witch to login. defaults to 8728
	returns:
		rosapi class
	exceptions:
		loginError. raised when failed to log in
	"""

	#self.log = logging.getLogger('mcm.configurator.{0}'.format(self.__class__.__name__))
	sock = socket.create_connection((address, port), 10)
	api = _rosapi.rosapi(sock)
	api.write('/login')
	response = api.read(parse=False)
	#check for valid response.
	#response must contain !done (as frst reply word), =ret=32 characters long response hash (as second reply word))
	if len(response) != 2 or len(response[1]) != 37:
		raise loginError('did not receive challenge response')
	chal = response[1].split('=', 2)[2]
	chal = chal.encode('UTF-8', 'strict')
	chal = unhexlify(chal)
	password = password.encode('UTF-8', 'strict')
	md = md5()
	md.update(b'\x00' + password + chal)
	password = hexlify(md.digest())
	password = password.decode('UTF-8', 'strict')
	api.write('/login', False)
	api.write('=name=' + username, False)
	api.write('=response=00' + password)
	response = api.read(parse=False)
	try:
		result = response[0]
	except IndexError:
		raise loginError('could not log in. unknown error')
	else:
		if result == '!done':
			return api
		elif result == '!trap':
			raise loginError('wrong username and/or password')
		else:
			raise loginError('unknown error {0}'.format(response))


__all__ = [k for k in list(locals().keys()) if not k.startswith('_')]

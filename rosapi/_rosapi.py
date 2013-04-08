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

import socket
import logging
from time import time
from struct import pack, unpack

from rosapi._exceptions import readError, writeError, apiError, cmdError

class rosapi:

	def __init__( self, sock, parent_logger = None ):
		self.sock = sock
		self.rw_timeout = 15
		self.sock_timeout = 10
		self.r_buffer = 1024
		self.w_buffer = 1024
		# prepare logging defaults to suppress all logging
		if parent_logger:
			# create logger with parent
			self.log = logging.getLogger( '{0}.{1}'.format( parent_logger, self.__class__.__name__ ) )
		else:
			# just create basic logger with our class name
			self.log = logging.getLogger( self.__class__.__name__ )
			# add null handler to suppress all messages
			self.log.addHandler( logging.NullHandler() )

	def talk( self, cmd, attrs = None ):
		"""
		this is a shortcut (wrapper) not to use write(), read() methods one after another. simply "talk" with RouterOS.
		takes:
			(string) cmd. eg /ip/address/print
			(dict) or (list) attrs default {}.
				dictionary with attribute -> value. every key value pair will be passed to api in form of =name=value
				list if order matters. eg. querry, every element in list is a word in api
		returns:
			returns parsed response from self.read()
		"""

		# map bollean types to string equivalents in routeros api
		mapping = {False: 'false', True: 'true', None: ''}
		# write level and if attrs is empty pass True to self.write, else False
		self.write( cmd, end = ( not bool( attrs ) ) )
		if attrs:
			count = len( attrs )
			i = 0
			if isinstance( attrs, dict ):
				for name, value in attrs.items():
					i += 1
					last = ( i == count )
					# write name and value (if bool is present convert to api equivalent) cast rest as string
					value = str( mapping.get( value, value ) )
					self.write( '={0}={1}'.format( name, value ), last )
			if isinstance( attrs, list ):
				for string in attrs:
					i += 1
					last = ( i == count )
					self.write( str( string ), last )
		return self.read()

	def writeLen( self, length ):
		"""
		encodes and writes int(length)  
		"""

		if length < 0x80:
			offset = -1
		elif length < 0x4000:
			length |= 0x8000
			offset = -2
		elif length < 0x200000:
			length |= 0xC00000
			offset = -3
		elif length < 0x10000000:
			length |= 0xE0000000
			offset = -4
		else:
			raise apiError( 'unable to encode length of {0}'.format( length ) )

		length = pack( '!I', length )[offset:]
		# write actual length in bytes to socket
		self.writeSock( length )

	def readLen( self ):
		"""
		read length and	return it as integer
		"""
		controll_byte = self.readSock( 1 )
		controll_byte_int = unpack( 'B', controll_byte )[0]

		if controll_byte_int < 128:
			return controll_byte_int
		elif controll_byte_int < 192:
			offset = b'\x00\x00'
			additional_bytes = self.readSock( 1 )
			XOR = 0x8000
		elif controll_byte_int < 224:
			offset = b'\x00'
			additional_bytes = self.readSock( 2 )
			XOR = 0xC00000
		elif controll_byte_int < 240:
			offset = b''
			additional_bytes = self.readSock( 3 )
			XOR = 0xE0000000
		else:
			raise apiError( 'unknown controll byte received {0}'.format( repr( controll_byte ) ) )

		length = offset + controll_byte + additional_bytes
		length = unpack( '!I', length )[0]
		length ^= XOR
		return length

	def mkBuffLst ( self, len, buffer ):
		"""
		make buffer list of integers based on given int(length) and int(buffer) > 0
		"""

		# how many full buffers
		tf_buffers = int( len / buffer )
		# full buffers summary
		tf_buff_sum = buffer * tf_buffers
		buff_lst = []

		for x in range( 0, tf_buffers ):
			buff_lst.append( buffer )

		if len > tf_buff_sum:
			buff_lst.append( len - tf_buff_sum )
		elif len < buffer:
			buff_lst.append( len )

		return buff_lst

	def writeSock( self, string ):
		"""
		bytes(string) string. must be bytes object
		"""

		i = 0
		str_len = len( string )
		timeout = time() + self.rw_timeout

		for buffer in self.mkBuffLst( str_len, self.w_buffer ):
			if time() > timeout:
				raise writeError( 'write timeout' )
			buf_string = string[i:i + buffer]
			self.log.debug( '<<< {0}'.format( repr( buf_string ) ) )
			b_sent = self.sock.send( buf_string )
			if b_sent == 0:
				raise writeError( 'failed to write to socket.' )
			i += buffer

		return

	def readSock( self, length ):
		"""
		int(length) how many bytes to read
		returns bytes object string
		"""

		ret_str = []
		timeout = time() + self.rw_timeout

		for buffer in self.mkBuffLst( length, self.r_buffer ):
			if time() > timeout:
				raise readError( 'read timeout' )
			buf_string = self.sock.recv( buffer )
			self.log.debug( '>>> {0}'.format( repr( buf_string ) ) )
			ret_str.append( buf_string )

		return b''.join( ret_str )

	def write( self, string, end = True ):
		"""
		takes:
			str(string) string to write
			(bool) end. True = send sentence end, False = wait for more data to write
		returns:
		"""

		self.writeLen( len( string ) )
		self.writeSock( string.encode( 'UTF-8', 'strict' ) )

		# if end is set to bool(true) send ending character chr(0)
		if end:
			self.log.debug( 'writing EOS' )
			self.writeSock( b'\x00' )
		return

	def read( self, parse = True ):
		"""
		takes:
			(bool) parse. whether to parse the response or not
		returns:
			(list) response. parsed or not depending on parse=
		"""

		response = []
		EOS = False
		while True:
			# read encoded length
			length = self.readLen()
			retword = ''

			if length > 0:
				retword = self.readSock( length )
				retword = retword.decode( 'UTF-8', 'strict' )
				response.append( retword )
				# make a note when got !done or !fatal this marks end of sentence
				if retword in ['!done', '!fatal']:
					EOS = True
			if ( not length and EOS ):
				break
		if parse:
			response = self.parseResponse( response )
		return response

	def parseResponse( self, response ):
		"""
		takes:
			(list) response. response to be parsed
		returns:
			(list) in list every data reply is a dictionary with key value pair
		exceptions:
			cmdError
		"""
		parsed_response = []
		index = -1
		for word in response:
			if word in ['!trap', '!re']:
				index += 1
				parsed_response.append( {} )
			elif word == '!done':
				break
			else:
				# split word by second occurence of '='
				word = word.split( '=', 2 )
				kw = word[1]
				val = word[2]
				parsed_response[index][kw] = self.typeCast( val )
		if '!trap' in response:
			msg = ', '.join( ' '.join( '{0}="{1}"'.format( k, v ) for ( k, v ) in inner.items() ) for inner in parsed_response )
			raise cmdError( msg )
		return parsed_response

	def typeCast( self, string ):
		"""cast strings into possibly int, boollean"""
		mapping = {'true': True, 'false': False}
		try:
			ret = int( string )
		except ValueError:
			ret = mapping.get( string, string )
		return ret

	def __del__( self ):
		"""disconnect garbage collecting"""
		self.close()

	def close( self ):
		'''
		disconnect and cleanup
		'''
		if self.sock._closed:
			return
		try:
			# send /quit command
			self.write( '/quit' )
			# read response without parsing
			self.read( parse = False )
		except socket.error:
			pass
		finally:
			# shutdown socket
			self.sock.shutdown( socket.SHUT_RDWR )
			self.sock.close()

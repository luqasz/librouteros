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

class cmdError( Exception ):
    '''
    Exception raised when execution of a command has failed.
    '''
    pass

class apiError( Exception ):
    '''
    Exception raised when some internal api error occurred.
    '''
    pass

class loginError( Exception ):
    '''
    Exception raised when login attempt failed. This can be also related to failure of socket connections.
    '''
    pass

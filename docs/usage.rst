Library usage
=============

.. note::

    This library comes with built in documentation. Run ``help(method)`` to get the docs.

Type casting
------------

Library automaticly casts values to/from python equivalents. Table below specifies how values are casted.

.. csv-table::
    :header: "Python", "Api"

    "False", "no/false"
    "True", "yes/true"
    "None", "''"
    "123",  "'123'"

Any type not specified in table above is converted to str.

Key names are also converted. All api attribute words that start with ``=.`` are converted to uppercase. For example ``=.id=*4`` will be converted to ``{ 'ID': '*4' }``. All uppercase dictionary keys will be converted to lowercase and a ``=.`` will be prefixed.

Basic usage
-----------

::

    from librouteros import connect

    api = connect( '1.1.1.1', 'admin', 'password' )
    addresses = api.run('/ip/address/print')
    # close the connestion
    api.close()


Printing elements
-----------------

::

    api.run( '/system/logging/action/print' )

    ({'ID': '*0',
    'default': True,
    'memory-lines': 100,
    'memory-stop-on-full': False,
    'name': 'memory',
    'target': 'memory'},
    {'ID': '*1',
    'default': True,
    'disk-file-count': 2,
    'disk-file-name': 'log',
    'disk-lines-per-file': 100,
    'disk-stop-on-full': False,
    'name': 'disk',
    'target': 'disk'},
    {'ID': '*2',
    'default': True,
    'name': 'echo',
    'remember': True,
    'target': 'echo'},
    {'ID': '*3',
    'bsd-syslog': False,
    'default': True,
    'name': 'remote',
    'remote-port': 514,
    'src-address': '0.0.0.0',
    'syslog-facility': 'daemon',
    'syslog-severity': 'auto',
    'syslog-time-format': 'bsd-syslog',
    'target': 'remote'})



Printing additional information such as stats.
::

    api.run( '/interface/ethernet/print', args={'stats':True} )

    {'ID': '*1',
    'arp': 'enabled',
    'auto-negotiation': True,
    'bandwidth': 'unlimited/unlimited',
    'default-name': 'sfp1',
    'disabled': True,
    'driver-rx-byte': 0,
    'driver-rx-packet': 0,
    'driver-tx-byte': 0,
    'driver-tx-packet': 0,
    'full-duplex': True,
    'l2mtu': 1598,
    'mac-address': 'D4:CA:6D:86:ED:04',
    'master-port': 'none',
    'mtu': 1500,
    'name': 'sfp1',
    'orig-mac-address': 'D4:CA:6D:86:ED:04',
    'running': False,
    'rx-1024-1518': 0,
    'rx-128-255': 0,
    'rx-1519-max': 0,
    'rx-256-511': 0,
    'rx-512-1023': 0,
    'rx-64': 0,
    'rx-65-127': 0,
    'rx-align-error': 0,
    'rx-broadcast': 0,
    'rx-bytes': 0,
    'rx-fcs-error': 0,
    'rx-fragment': 0,
    'rx-multicast': 0,
    'rx-overflow': 0,
    'rx-pause': 0,
    'rx-too-long': 0,
    'rx-too-short': 0,
    'sfp-rate-select': True,
    'speed': '100Mbps',
    'switch': 'switch1',
    'tx-1024-1518': 0,
    'tx-128-255': 0,
    'tx-1519-max': 0,
    'tx-256-511': 0,
    'tx-512-1023': 0,
    'tx-64': 0,
    'tx-65-127': 0,
    'tx-broadcast': 0,
    'tx-bytes': 0,
    'tx-collision': 0,
    'tx-deferred': 0,
    'tx-excessive-collision': 0,
    'tx-excessive-deferred': 0,
    'tx-late-collision': 0,
    'tx-multicast': 0,
    'tx-multiple-collision': 0,
    'tx-pause': 0,
    'tx-single-collision': 0,
    'tx-too-long': 0,
    'tx-underrun': 0},

Adding element
--------------

::

    data = { 'interface':'ether1', 'address':'172.31.31.1/24' }
    ID = api.run( '/ip/address/add', data )
    # get newly created ID
    ID[0]['ret']
    '*23'

Removing element
----------------

::

    idlist = ','.join( '*12', '*1' )
    api.run( '/ip/address/remove', {'ID':idlist} )

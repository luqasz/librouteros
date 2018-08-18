Library usage
=============

.. note::

    This library comes with built in documentation. Run ``help(method)`` to get the docs.

Type casting
------------

Python booleans are converted according to this table:

====== ========= ========
python direction api
====== ========= ========
False  <-        false,no
True   <-        true,yes
False  ->        no
True   ->        yes
====== ========= ========

Integers are converted to python int objects.

Connecting
----------

.. code-block:: python

    from librouteros import connect

    api = connect(username='admin', password='abc', host='some.address.com')

For SSL/TLS you need to create a ssl.SSLContext instance and pass it to ``connect()``.
Bare minimal requirement for ssl to work (without certificates).

.. code-block:: python

    import ssl
    from librouteros import connect

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    ctx.set_ciphers('ADH')
    api = connect(
        username='admin',
        password='abc',
        host='some.address.com',
        ssl_wrapper=ctx.wrap_socket,
        port=8729
        )


Printing elements
-----------------

.. code-block:: python

    api(cmd='/interface/print', stats=True)
    ({'.id': '*1',
    'bytes': '418152/157562',
    'comment': '',
    'disabled': False,
    'drops': '0/0',
    'dynamic': False,
    'errors': '0/0',
    'mtu': 1500,
    'name': 'ether1',
    'packets': '3081/1479',
    'running': True,
    'type': 'ether'},)

    api(cmd='/interface/print')
    ({'.id': '*1',
    'comment': '',
    'disabled': False,
    'dynamic': False,
    'mtu': 1500,
    'name': 'ether1',
    'running': True,
    'type': 'ether'},)

If you want to pass parameters that start with a dot character you can do it in this way:

.. code-block:: python

    params = {'disabled': True, '.id' :'*7'}
    api(cmd='/ip/firewall/nat/set', **params)

Note that ``.id`` must always be passed as read from API. They usually start with a ``*`` followed by a number.
Keep in mind that they do change across reboots. As a rule of thumb, always read them first.

Adding element
--------------

.. code-block:: python

    data = {'interface':'ether1', 'address':'172.31.31.1/24'}
    ID = api.run('/ip/address/add', data)
    # get newly created ID
    ID[0]['ret']
    '*23'

Removing element
----------------

.. code-block:: python

    params = {'.id' :'*7'}
    api.run('/ip/address/remove', **params)

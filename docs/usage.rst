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

Before connecting, ``api-ssl`` service on routeros must be enabled.
For more information on how to generate certificates see `MikroTik wiki <https://wiki.mikrotik.com/wiki/Manual:Create_Certificates>`_.
After that, create your default `SSLContext <https://docs.python.org/library/ssl.html#ssl.create_default_context>`_ and fine tune for your needs. Code below allows connecting to API without ceritficate.

.. code-block:: python

    import ssl
    from librouteros import connect

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.set_ciphers('ADH:@SECLEVEL=0')
    api = connect(
        username='admin',
        password='abc',
        host='some.address.com',
        ssl_wrapper=ctx.wrap_socket,
        port=8729
        )


New auth method
---------------

Starting from routeros ``6.43``, plain text auth method was introduced. By default library will use plain text method. You can force library to use token method:

.. code-block:: python

    from librouteros.login import plain, token

    # for new (plain text password)
    method = plain
    # for old (with token)
    method = token
    api = connect(username='admin', password='abc', host='some.address.com', login_method=method)


Printing elements
-----------------
Calling api will yield each result.

.. code-block:: python

    tuple(api(cmd='/interface/print', stats=True))
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

    tuple(api(cmd='/interface/print'))
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

    result = api('/ip/address/add', interface='ether1', address='172.31.31.1/24')
    # get newly created .id
    tuple(result)[0]['ret']
    '*23'

Removing element
----------------

.. code-block:: python

    params = {'.id' :'*7'}
    tuple(api('/ip/address/remove', **params))

Plain api command
-----------------

Method allows to pass a plain (raw) command with command words to API. Usefull for writing custom queries.

.. code-block:: python

    tuple(api.rawCmd('/ip/address/print', '?=address=1.1.1.1'))

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

Starting from routeros ``6.43``, new auth method was introduced. By default library will try to login using old method first (with token), then new (using plain text password) method. You can force library to try only one method:

.. code-block:: python

    from librouteros.login import login_plain, login_token

    # for new (plain text password)
    method = (login_plain, )
    # for old (with token)
    method = (login_token, )
    api = connect(username='admin', password='abc', host='some.address.com', login_methods=method)


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

    result = api('/ip/address/add', interface='ether1', address='172.31.31.1/24')
    # get newly created .id
    result[0]['ret']
    '*23'

Removing element
----------------

.. code-block:: python

    params = {'.id' :'*7'}
    api('/ip/address/remove', **params)

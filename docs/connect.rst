Connect
=======

Unencrypted
-----------

.. code-block:: python

    from librouteros import connect
    api = connect(
        username='admin',
        password='abc',
        host='some.address.com',
    )

Encrypted
---------

Before connecting, ``api-ssl`` service on routeros must be enabled.
For more information on how to generate certificates see
`MikroTik wiki <https://wiki.mikrotik.com/wiki/Manual:Create_Certificates>`_.
After that, create your default `SSLContext <https://docs.python.org/library/ssl.html#ssl.create_default_context>`_
and fine tune for your needs. Code below allows connecting to API without ceritficate.

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

Auth methods
------------

Starting from routeros ``6.43``, token auth method was replaced by plain text.
By default library will use plain text method. You can force library to use token method:

.. code-block:: python

    from librouteros.login import plain, token

    # for post 6.42 (plain text password)
    method = plain
    # for pre 6.43 (with token)
    method = token
    api = connect(username='admin', password='abc', host='some.address.com', login_method=method)

.. note::

    Library will not try different methods untill it will log in.

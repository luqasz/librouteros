.. image:: https://travis-ci.org/luqasz/librouteros.svg?branch=master
    :target: https://travis-ci.org/luqasz/librouteros
    :alt: Tests

.. image:: https://img.shields.io/pypi/v/librouteros.svg
    :target: https://pypi.python.org/pypi/librouteros/
    :alt: Latest PyPI version

.. image:: https://img.shields.io/pypi/pyversions/librouteros.svg
    :target: https://pypi.python.org/pypi/librouteros/
    :alt: Supported Python Versions

.. image:: https://img.shields.io/pypi/l/librouteros.svg
    :target: https://pypi.python.org/pypi/librouteros/
    :alt: License

About
=====
Python implementation of `routeros api <http://wiki.mikrotik.com/wiki/API>`_. This library uses `semantic versioning <http://semver.org/>`_. On major version things may break, so pin version in dependencies.


Usage
=====

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
    api = connect(username='admin', password='abc', host='some.address.com', ssl_wrapper=ctx.wrap_socket, port=8729)


Api usage.

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

    api.close()

If you want to pass parameters that start with a dot character you can do it in this way:

.. code-block:: python

    params = {'disabled': True, '.id' :'*7'}
    api(cmd='/ip/firewall/nat/set', **params)

Note that ``.id`` must always be passed as read from API. They usually start with a ``*`` followed by a number.
Keep in mind that they do change across reboots. As a rule of thumb, always read them first.


Booleans conversions
====================

Python booleans are converted according to this table:

====== ========= ========
python direction api
====== ========= ========
False  <-        false,no
True   <-        true,yes
False  ->        no
True   ->        yes
====== ========= ========


Contributing
============
To submit a feature requests or a bug report, please use issues from within github. If you would like to submit a patch please contact author or use pull request.

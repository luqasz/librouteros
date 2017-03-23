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
Python implementation of `routeros api <http://wiki.mikrotik.com/wiki/API>`_.
This library uses `semantic versioning <http://semver.org/>`_. On major version things may break, so pin version in dependencies.

Usage
=====

.. code-block:: python

    In [1]: from librouteros import connect

    In [2]: api = connect(host='192.168.56.200', username='admin', password='abc')

    In [4]: api(cmd='/interface/print', stats=True)
    Out[4]:
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

    In [5]: api(cmd='/interface/print')
    Out[5]:
      ({'.id': '*1',
      'comment': '',
      'disabled': False,
      'dynamic': False,
      'mtu': 1500,
      'name': 'ether1',
      'running': True,
      'type': 'ether'},)

    In [7]: api.close()

    In [8]:


If you want to pass parameters that strart with a dot character you can do it in this way:

.. code-block:: python

    params = {'disabled': True, '.id' :'7'}
    api(cmd='/ip/firewall/nat/set', **params)


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

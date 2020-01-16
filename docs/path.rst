Path object
===========

``Path`` object represents absolute command path within routeros. e.g. ``/ip/address``.
You can traverse down in tree with ``join()`` method.
Works same as python `join() <https://docs.python.org/3/library/os.path.html#os.path.join>`_.

.. code-block:: python

    # First create desired path.
    interfaces = api.path('interface')
    # Traverse down into /interfaces/ethernet
    ethernet = interfaces.join('ethernet')

    # path() and join() accepts multiple arguments
    ips = api.path('ip', 'address')

Get all
-------

.. code-block:: python

    # Path objects are iterable
    tuple(interfaces)
    # This also will work, as well as anything else you can do with iterables
    for item in interfaces:
        print(item)

Add
---

.. code-block:: python

    # Will return newly created .id
    path.add(interface='ether1', address='172.31.31.1/24')

Remove
------

.. code-block:: python

    # Pass each .id as an argument.
    path.remove('*1', '*2')

.. note::

    ``.id`` change on reboot. Always read them first.

Update
------

.. code-block:: python

    params = {'disabled': True, '.id' :'*7'}
    path.update(**params)

.. note::

    ``.id`` change on reboot. Always read them first.

Arbitrary command
-----------------
For all other commands, call ``Path`` object directly.
Remember to consume the result since it returns a generator.
As a first argument, pass command that you wish to run without absolute path.

.. code-block:: python

    script = api.path('system', 'script')
    # Will run /system/script/run with desired .id
    tuple(script('run', **{'.id': '*1'}))

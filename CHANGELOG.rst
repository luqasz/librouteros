3.2.0
----------

* Ignore character decoding errors

3.1.0
----------

* Add In operator

3.0.2
----------

- Fix generator yielding #94

3.0.1
__________

- Add typing annotations


3.0.0
----------

- Introduce query support.
- Path object for easy query and common operations.
- yield each item instead of returning tuple of items. Greatly reduces memory usage.
- Drop pre python 3.6 support.
- Replace pylava with pylint.
- Add yapf formatter.
- Replace py.path with builtin pathlib.
- connect() accepts only one login_method parameter.
- Drop socker exceptions wrapping.
- Remove ConnectionError exception.
- Renamed LibError to LibRouterosError.
- Changed exceptions inheritance.
- Removed joinPath()

2.4.0
----------

- Add query support. #11

2.3.1
----------

- Fix raising TrapError when failed to login. #63

2.3.0
----------

- Add rawCmd() method for passing custom queries.

2.2.0
----------

- Excplicit login_method parameter for login using new or old auth method.

2.1.1
----------

- Fix testing with pip >= 18.x

2.1.0
----------

- Support new auth method introduced in 6.43

2.0.0
------

- Drop support for python 3.2, 3.3
- Added ssl / apis support

1.0.5
------

- Fix loop in SocketTransport.read() (pull request #23)

1.0.4
------

- Fix multiple byte word encoding during reading (issue #12)

1.0.3
------

- Provide option to use user defined encoding

1.0.2
------

- Fix E722 do not use bare except [pep8]
- Test with python 3.6
- Integration tests with qemu emulated RouterOs image
- Pin setuptools to higher version

1.0.1
------

- First release

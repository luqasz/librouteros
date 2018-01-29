2.0.0
------

- Drop support for python 3.2, 3.3
- Removed connect() function with login()
- Ability to pass connected socket (ssl or plain) to login()

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

Documentation
=============

Documentation resides over at
`readthedocs <https://librouteros.readthedocs.io/>`_

Async Usage
connection = await async_connect(
        host="127.0.0.1",
        username="admin",
        password="admin",
        timeout=30
    )

hotspot_user_path = connection.path('/ip/hotspot/user')
hotspot_users = [user async for user in hotspot_user_path.select('.id')]

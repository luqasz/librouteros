from librouteros.query import Key


def test_hostname(routeros):
    data = routeros('/system/identity/print')
    assert tuple(data)[0]['name'] == 'MikroTik'


def test_query(routeros):
    new_address = '172.16.1.1/24'
    ip = routeros(
        '/ip/address/add',
        address=new_address,
        interface='ether1',
    )
    created_id = tuple(ip)[0]['ret']

    ID = Key('.id')
    address = Key('address')
    query = routeros.path('/ip/address').select(ID, address).where(ID == created_id, address == new_address)
    selected_data = tuple(query)
    assert len(selected_data) == 1
    assert selected_data[0]['.id'] == created_id
    assert selected_data[0]['address'] == new_address


def test_long_word(routeros):
    r"""
    Assert that when word length is encoded with \x00 in it,
    library should decode this without errors.

    Create a entry with long word length (256)
    resulting in word encoding of \x81\00.
    Check if when reading back, comment is same when set.
    """
    long_value = 'a' * (256 - len('=comment='))
    data = routeros(
        '/ip/address/add',
        address='172.16.1.1/24',
        interface='ether1',
        comment=long_value,
    )
    ID = tuple(data)[0]['ret']
    for row in routeros('/ip/address/print'):
        if row['.id'] == ID:
            assert row['comment'] == long_value

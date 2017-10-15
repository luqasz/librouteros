def test_hostname(routeros):
    data = routeros('/system/identity/print')
    assert data[0]['name'] == 'MikroTik'


def test_long_word(routeros):
    """
    Assert that when word length is encoded with \x00 in it,
    library should decode this without errors.

    Create a entry with long word length (256)
    resulting in word encoding of \x81\00.
    Check if when reading back, comment is same when set.
    """
    long_value = 'a' * (256 - len('=comment='))
    ID = routeros(
            '/ip/address/add',
            address='172.16.1.1/24',
            interface='ether1',
            comment=long_value
        )[0]['ret']
    for row in routeros('/ip/address/print'):
        if row['.id'] == ID:
            assert row['comment'] == long_value

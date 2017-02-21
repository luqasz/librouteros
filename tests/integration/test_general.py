def test_hostname(routeros):
    data = routeros('/system/identity/print')
    assert data[0]['name'] == 'MikroTik'

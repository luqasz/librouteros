from sys import (
    version_info,
)

import pytest


@pytest.mark.skipif(version_info.major >= 3, reason='collections.ChainMap is in >= 3.3')
def test_chainmap_installed(installed_packages):
    assert 'chainmap' in installed_packages


@pytest.mark.skipif(version_info.major < 3, reason='ChainMap installed from pip')
def test_chainmap_not_installed(installed_packages):
    assert 'chainmap' not in installed_packages

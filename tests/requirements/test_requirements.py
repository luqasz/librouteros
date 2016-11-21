import pip
import pytest
from sys import version_info

pyversion = version_info.major, version_info.minor


@pytest.mark.skipif(pyversion > (3, 2), reason='collections.ChainMap is in >= 3.3')
def test_chainmap_installed():
    pkgs = pip.utils.get_installed_distributions(local_only=True, include_editables=False)
    assert 'chainmap' in (pkg.key for pkg in pkgs)


@pytest.mark.skipif(pyversion < (3, 3), reason='ChainMap installed from pip')
def test_chainmap_not_installed():
    pkgs = pip.utils.get_installed_distributions(local_only=True, include_editables=False)
    assert 'chainmap' not in (pkg.key for pkg in pkgs)

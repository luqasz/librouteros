import sys
from subprocess import (
    check_output,
)

import pytest


@pytest.fixture
def installed_packages():
    pkgs = []
    pip_executable = [sys.executable, '-m', 'pip']
    result = check_output(pip_executable + ["freeze", "--local", "--all"])
    for line in result.decode().splitlines():
        if '==' in line:
            pkg, version = line.split('==', 1)
            pkgs.append(pkg)

    return pkgs

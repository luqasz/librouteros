#!/usr/bin/env bash
set -Eeuo pipefail

python setup.py sdist
twine upload dist/*

#!/bin/sh

for ver in 3.8 3.9 3.10 3.11 3.12
do
  docker buildx build --platform linux/amd64,linux/arm64 --push -t lukaszkostka/librouteros:${ver} -f docker/${ver}.dockerfile .
done

#!/bin/sh

for ver in 3.6 3.7 3.8 3.9
do
  docker buildx build --platform linux/amd64,linux/arm64 --push -t lukaszkostka/librouteros:${ver} -f docker/${ver}.dockerfile .
done

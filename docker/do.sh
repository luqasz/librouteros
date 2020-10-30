#!/bin/sh

for ver in 3.6 3.7 3.8
do
  docker build -t lukaszkostka/librouteros:${ver} -f docker/${ver}.dockerfile .
  docker push lukaszkostka/librouteros:${ver}
done

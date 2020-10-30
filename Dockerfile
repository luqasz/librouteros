FROM debian:buster

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update
RUN apt-get install -y --no-install-recommends \
      python3 \
      pipenv \
      qemu-system-i386 \
      qemu-utils

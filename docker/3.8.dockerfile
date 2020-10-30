FROM python:3.8

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update
RUN apt-get install -y --no-install-recommends \
      qemu-system-i386 \
      qemu-utils \
      wget \
      git-lfs

RUN pip install pipenv
RUN pip install twine

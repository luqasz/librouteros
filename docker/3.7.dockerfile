FROM python:3.7

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update
RUN apt-get install -y --no-install-recommends \
      qemu-system-i386 \
      qemu-utils \
      wget

COPY images/*.qcow2 /opt/
RUN pip install -U setuptools pip
RUN pip install twine pipenv

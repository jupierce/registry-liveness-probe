FROM quay.io/centos/centos:stream9
COPY requirements.txt /tmp
COPY registry-liveness-probe.py /usr/bin/registry-liveness-probe.py
RUN chmod +x /usr/bin/registry-liveness-probe.py && dnf install -y python3 python3-pip && pip install -r /tmp/requirements.txt
ENTRYPOINT /usr/bin/registry-liveness-probe.py
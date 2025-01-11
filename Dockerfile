FROM quay.io/centos/centos:stream9
ADD https://mirror.openshift.com/pub/openshift-v4/amd64/clients/ocp/stable-4.17/openshift-client-linux.tar.gz /tmp/oc-client.tgz
RUN cd /usr/bin && tar zxvf /tmp/oc-client.tgz && chmod +x oc && rm -f /tmp/oc-client.tgz
COPY requirements.txt /tmp
RUN dnf install -y python3 python3-pip && pip install -r /tmp/requirements.txt
COPY registry-liveness-probe.py /usr/bin/registry-liveness-probe.py
RUN chmod +x /usr/bin/registry-liveness-probe.py
ENTRYPOINT ["python3", "/usr/bin/registry-liveness-probe.py"]
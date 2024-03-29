FROM ubuntu:20.04

LABEL maintainer="emil@jacero.se"

ARG DEBIAN_FRONTEND=noninteractive
ARG APT_KEY_DONT_WARN_ON_DANGEROUS_USAGE=DontWarn
# Build arguments with sane defaults
ARG PDNS_VERSION=45

# NOTE: DO NOT OVERWRITE THIS VARIABLE... EVER!
ENV POWERDNS_VERSION=$PDNS_VERSION
# Sane defaults
ENV LOG_LEVEL=INFO
ENV EXEC_MODE=DOCKER

# Install and upgrade
#RUN apt update && apt -y install tzdata
RUN apt update && apt install -y tzdata ca-certificates curl wget gnupg2 jq dnsutils python3 python3-pip python3-psycopg2 vim && apt -y upgrade
RUN touch /etc/apt/sources.list.d/pdns.list && echo deb [arch=amd64] http://repo.powerdns.com/ubuntu focal-auth-$PDNS_VERSION main > /etc/apt/sources.list.d/pdns.list
RUN echo "Package: pdns-*" >> /etc/apt/preferences.d/pdns && \
    echo "Pin: origin repo.powerdns.com" >> /etc/apt/preferences.d/pdns && \
    echo "Pin-Priority: 600" >> /etc/apt/preferences.d/pdns
RUN curl -fsSL https://repo.powerdns.com/FD380FBB-pub.asc | apt-key add - && apt-get update
RUN apt -y install pdns-server pdns-backend-pgsql pdns-backend-sqlite3 postgresql-client

# Set Timezone
ENV TZ=Etc/UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Installing python modules
ADD requirements.txt /
RUN pip3 install -r requirements.txt

# Prepare directories for PowerDNS
RUN rm -rf /etc/powerdns; \
    mkdir -p /etc/powerdns/pdns.d && chown -R 101:101 /etc/powerdns && chmod 755 /etc/powerdns; \
    mkdir -p /var/run/pdns-authorative && chown -R 101:101 /var/run/pdns-authorative; \
    mkdir -p /var/run/powerdns-authorative && chown -R 101:101 /var/run/powerdns-authorative

# Add src
ADD src /app
RUN chown -R 101:101 /app; touch /pdns.conf && chown -R 101:101 /pdns.conf

# USER 101:101  # Disabled to allow CAP_NET_BIND_SERVICE
EXPOSE 53/tcp 53/udp 8001/tcp
WORKDIR /app
STOPSIGNAL SIGTERM
ENTRYPOINT /app/entrypoint.py

[![GitHub license](https://img.shields.io/github/license/emil-jacero/powerdns-auth-docker)](https://github.com/emil-jacero/powerdns-auth-docker/blob/master/LICENSE) [![GitHub stars](https://img.shields.io/github/stars/emil-jacero/powerdns-auth-docker)](https://github.com/emil-jacero/powerdns-auth-docker/stargazers) [![GitHub issues](https://img.shields.io/github/issues/emil-jacero/powerdns-auth-docker)](https://github.com/emil-jacero/powerdns-auth-docker/issues)

# powerdns-auth-docker
This is a PowerDNS authoritative docker image designed to handle minor and major updates seamlessly.

## Supported Architectures
The images are built and tested on multiple platforms.



| Architecture | Tag |
| :----: | --- |
| x86-64 | amd64-latest |
| arm64 | arm64v8-latest |

## Version Tags

This image provides various versions that are available via tags. `latest` tag usually provides the latest stable version.

| Tag | Description |
| :----: | --- |
| amd64-latest | Latest stable version |
| amd64-4.2.x | Latest micro release of 4.2 |
| amd64-4.1.x | Latest micro release of 4.1 |
| arm64v8-latest | Latest stable version |
| arm64v8-4.2.x | Latest micro release of 4.2 |
| arm64v8-4.1.x | Latest micro release of 4.1 |

## Environment variables
| Name | Value | Default |
| :----: | --- | --- |
| `PDNS_PGSQL_HOST` | Hostname/ip of the database | Name of the DB container |
| `PDNS_PGSQL_PORT` | Port of the database | 5432 |
| `PDNS_PGSQL_DBNAME` | Database name | pdns |
| `PDNS_PGSQL_USER` | Database username | pdns |
| `PDNS_PGSQL_PASSWORD` | Database password | supersecretpsqlpw |
| `ENV_PDNS_DNSSEC` | Do you want DNSSEC? | yes |
| `ENV_PDNS_API_PORT` | PowerDNS API port | 8001 |
| `ENV_PDNS_API_KEY` | PowerDNS API key | supersecretapikey |
| `ENV_PDNS_AXFR_IPS` | PowerDNS slave IP addresses | x.x.x.x |
| `ENV_PDNS_MODE` | What mode to start PowerDNS in | MASTER / SLAVE |
| `ENV_PDNS_MASTER_IP` | PowerDNS master IP address (Only needed when `ENV_PDNS_MODE` is SLAVE) | x.x.x.x |
| `ENV_PDNS_MASTER_NAMESERVER` | PowerDNS master nameserver (Only needed when `ENV_PDNS_MODE` is SLAVE) | ns1.example.com |
| `ENV_PDNS_MASTER_ACCOUNT` | PowerDNS master account (Only needed when `ENV_PDNS_MODE` is SLAVE) | example |

## Usage
### Example Masters
    version: '3.1'
    
    volumes:
      db-pdns-auth-master:
      pdns-auth-master:
    
    networks:
      dns:
        ipam:
          driver: default
          config:
            - subnet: "192.168.254.0/24"
    
    services:
      db-pdns-auth-master:
        container_name: db-pdns-auth-master
        image: postgres:11
        restart: always
        networks:
          - dns
        environment:
          POSTGRES_USER: pdns
          POSTGRES_PASSWORD: supersecretpsqlpw
          POSTGRES_DB: pdns
        volumes:
          - "db-pdns-auth-master:/var/lib/postgresql/data"
    
    
      pdns-auth-master:
        container_name: pdns-auth-master
        image: emil-jacero/powerdns-auth-gpgsql:amd64-4.1.x
        restart: always
        depends_on:
          - db-pdns-auth-master
        networks:
          - dns
        environment:
          PDNS_PGSQL_HOST: db-pdns-auth-master
          PDNS_PGSQL_PORT: 5432
          PDNS_PGSQL_DBNAME: pdns
          PDNS_PGSQL_USER: pdns
          PDNS_PGSQL_PASSWORD: supersecretpsqlpw
          ENV_PDNS_DNSSEC: "yes"
          ENV_PDNS_API_PORT: 8001
          ENV_PDNS_API_KEY: supersecretapikey
          ENV_PDNS_AXFR_IPS: x.x.x.x # IPs of slaves
          ENV_PDNS_MODE: MASTER
        ports:
          - 8001:8001/tcp
          - 53:53/tcp
          - 53:53/udp
        volumes:
          - "pdns-auth-master:/var/run/pdns"


### Example Master
    version: '3.1'
    
    volumes:
      db-pdns-auth-slave:
      pdns-auth-slave:
    
    networks:
      dns:
        ipam:
          driver: default
          config:
            - subnet: "192.168.253.0/24"
    
    services:
      db-pdns-auth-slave:
        container_name: db-pdns-auth-slave
        image: postgres:11
        restart: always
        networks:
          - dns
        environment:
          POSTGRES_USER: pdns
          POSTGRES_PASSWORD: supersecretpsqlpw
          POSTGRES_DB: pdns
        volumes:
          - "db-pdns-auth-master:/var/lib/postgresql/data"
    
    
      pdns-auth-slave:
        container_name: pdns-auth-slave
        image: emil-jacero/powerdns-auth-gpgsql:amd64-4.1.x
        restart: always
        depends_on:
          - db-pdns-auth-slave
        networks:
          - dns
        environment:
          PDNS_PGSQL_HOST: db-pdns-auth-slave
          PDNS_PGSQL_PORT: 5432
          PDNS_PGSQL_DBNAME: pdns
          PDNS_PGSQL_USER: pdns
          PDNS_PGSQL_PASSWORD: supersecretpsqlpw
          ENV_PDNS_DNSSEC: "yes"
          ENV_PDNS_API_PORT: 8001
          ENV_PDNS_API_KEY: supersecretapikey
          ENV_PDNS_MODE: SLAVE
          ENV_PDNS_MASTER_IP: x.x.x.x
          ENV_PDNS_MASTER_NAMESERVER: ns1.example.com
          ENV_PDNS_MASTER_ACCOUNT: example
        ports:
          - 8001:8001/tcp
          - 53:53/tcp
          - 53:53/udp
        volumes:
          - "pdns-auth-slave:/var/run/pdns"

# powerdns-auth-docker
This is a PowerDNS authoritative docker image designed to handle minor and major updates seamlessly.

## Example Masters
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
        image: emil-jacero/powerdns-auth-gpgsql:amd64_4.1.x
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


## Example Master
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
        image: emil-jacero/powerdns-auth-gpgsql:amd64_4.1.x
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

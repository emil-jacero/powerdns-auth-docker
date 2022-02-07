[![GitHub license](https://img.shields.io/github/license/emil-jacero/powerdns-auth-docker)](https://github.com/emil-jacero/powerdns-auth-docker/blob/master/LICENSE) [![GitHub stars](https://img.shields.io/github/stars/emil-jacero/powerdns-auth-docker)](https://github.com/emil-jacero/powerdns-auth-docker/stargazers) [![GitHub issues](https://img.shields.io/github/issues/emil-jacero/powerdns-auth-docker)](https://github.com/emil-jacero/powerdns-auth-docker/issues)

# powerdns-auth-docker

This is a PowerDNS authoritative docker image designed to handle minor and major updates seamlessly.

## Related projects

- [powerdns-recursor-docker](https://github.com/emil-jacero/powerdns-recursor-docker)
- [powerdns-dnsdist-docker](https://github.com/emil-jacero/powerdns-dnsdist-docker)

## Supported Architectures

The images are built and tested on multiple platforms.

| Architecture | Tag |
| :----: | --- |
| x86-64 | amd64-latest |
| arm64 | arm64v8-latest |
| armv7l | armhf-latest |

## Version Tags

This image provides various versions that are available via tags. `latest` tag provides the latest stable version.

| Tag | Description |
| :----: | --- |
| amd64-latest | Latest stable version |
| amd64-4.6.x | Latest micro release of 4.6 |
| amd64-4.5.x | Latest micro release of 4.5 |

## Configuration

You configure using environment variables or as a mounted volume. The environment variable will be converted to the nameing scheme PowerDNS is using.

### Environment variable example

First set the `EXEC_MODE` to `ENV` (Default)

**Docker env:** `ENV_LOCAL_ADDRESS=0.0.0.0` or `ENV_LOCAL_ADDRESS: 0.0.0.0`

**PDNS config:** `local-address=0.0.0.0`

### Mounted volume example

First set the `EXEC_MODE` to `VOL`
Save the below config to a file and mount to `/etc/powerdns/pdns.conf`

```
primary=yes
secondary=no
launch=gsqlite3
gsqlite3-database=/var/lib/powerdns/auth.db
gsqlite3-pragma-synchronous=0
local-address=0.0.0.0
local-port=53
```

---

## Required environment variables

| Name | Value | Default |
| :----: | --- | --- |
| `TZ` | Timezone | `Etc/UTC` |
| `EXEC_MODE` | Configuring with Environment variables or config file? (`ENV` or `VOL`) | `ENV` |

## Required environment variables for secondaries

| Name | Value | Default |
| :----: | --- | --- |
| `AUTOSECONDARY_IP` | The IP of the primary DNS server | N/A |
| `AUTOSECONDARY_NAMESERVER` | The name of the primary DNS server  | N/A |
| `AUTOSECONDARY_ACCOUNT` | The account used on the primary DNS server | N/A |

## Common environment variables

| Name | Value | Default |
| :----: | --- | --- |
| `ENV_PRIMARY` | [Docs](https://doc.powerdns.com/authoritative/settings.html#primary) | `yes` |
| `ENV_SECONDARY` | [Docs](https://doc.powerdns.com/authoritative/settings.html#secondary) | `no` |
| `ENV_LAUNCH` | [Docs](https://doc.powerdns.com/authoritative/settings.html#launch) | `gsqlite3` |
| `ENV_GSQLITE3_DATABASE` | [Docs](https://doc.powerdns.com/authoritative/backends/generic-sqlite3.html) | `"/var/lib/powerdns/auth.db"` |
| `ENV_GSQLITE3_PRAGMA_SYNCHRONOUS` | [Docs](https://doc.powerdns.com/authoritative/backends/generic-sqlite3.html) | `0` |
| `ENV_LOCAL_ADDRESS` | [Docs](https://doc.powerdns.com/authoritative/settings.html#local-address) | `"0.0.0.0"` |
| `ENV_LOCAL_PORT` | [Docs](https://doc.powerdns.com/authoritative/settings.html#local-port) | `53` |

## Database support

- SQLite3
- PostgreSQL

## Examples

### Single authoritative primary with SQLite

```
version: '3'
services:
  pdns-auth:
    container_name: pdns-auth
    image: emiljacero/powerdns-auth-docker:amd64-latest
    restart: always
    network_mode: host
    environment:
      TZ: Etc/UTC
      ENV_PRIMARY: "yes"
      ENV_SECONDARY: "no"
      ENV_LAUNCH: gsqlite3
      ENV_GSQLITE3_DATABASE: "/var/lib/powerdns/auth.db"
      ENV_GSQLITE3_PRAGMA_SYNCHRONOUS: 0
      ENV_ENTROPY_SOURCE: /dev/urandom
      ENV_LOCAL_ADDRESS: 192.168.100.20
      ENV_LOCAL_PORT: 53
    volumes:
      - ./db:/var/lib/powerdns
```

### Single authoritative secondary with SQLite

Running a secondary authoritative requires the extra environment variables beginning with `AUTOSECONDARY`.

```
version: '3'
services:
  pdns-auth:
    container_name: pdns-auth
    image: emiljacero/powerdns-auth-docker:amd64-latest
    restart: always
    network_mode: host
    environment:
      TZ: Etc/UTC
      AUTOSECONDARY_IP: 192.168.100.10
      AUTOSECONDARY_NAMESERVER: ns1.example.com
      AUTOSECONDARY_ACCOUNT: Example
      ENV_PRIMARY: "no"
      ENV_SECONDARY: "yes"
      ENV_AUTOSECONDARY: "yes"
      ENV_LAUNCH: gsqlite3
      ENV_GSQLITE3_DATABASE: "/var/lib/powerdns/auth.db"
      ENV_GSQLITE3_PRAGMA_SYNCHRONOUS: 0
      ENV_ENTROPY_SOURCE: /dev/urandom
      ENV_LOCAL_ADDRESS: 192.168.100.20
      ENV_LOCAL_PORT: 53
    volumes:
      - ./db:/var/lib/powerdns
```

### Single authoritative secondary with SQLite and PowerDNS recursor

Please note that the authoritative server is listening on 5300. That means notifications has to be sent towards `192.168.100.20:5300`.

```
version: '3'
services:
  pdns-auth:
    container_name: pdns-auth
    image: emiljacero/powerdns-auth-docker:amd64-latest
    restart: always
    network_mode: host
    environment:
      TZ: Etc/UTC
      AUTOSECONDARY_IP: 192.168.100.10
      AUTOSECONDARY_NAMESERVER: ns1.example.com
      AUTOSECONDARY_ACCOUNT: Example
      ENV_PRIMARY: "no"
      ENV_SECONDARY: "yes"
      ENV_AUTOSECONDARY: "yes"
      ENV_LAUNCH: gsqlite3
      ENV_GSQLITE3_DATABASE: "/var/lib/powerdns/auth.db"
      ENV_GSQLITE3_PRAGMA_SYNCHRONOUS: 0
      ENV_ENTROPY_SOURCE: /dev/urandom
      ENV_SOCKET_DIR: /var/run/powerdns-authorative
      ENV_LOCAL_ADDRESS: 192.168.100.20
      ENV_LOCAL_PORT: 5300
    volumes:
      - ./db:/var/lib/powerdns

  pdns-recursor:
    container_name: pdns-recursor
    image: emiljacero/powerdns-recursor-docker:amd64-latest
    restart: always
    depends_on:
      - pdns-auth
    network_mode: host
    environment:
      TZ: Etc/UTC
      ENV_ALLOW_FROM: 127.0.0.0/8, 10.0.0.0/8, 100.64.0.0/10, 169.254.0.0/16,
        192.168.0.0/16, 172.16.0.0/12, ::1/128, fc00::/7, fe80::/10
      ENV_HINT_FILE: /var/named.root
      ENV_INCLUDE_DIR: /etc/powerdns/recursor.d
      ENV_FORWARD_ZONES_FILE: /etc/powerdns/forward.conf
      ENV_ENTROPY_SOURCE: /dev/urandom
      ENV_SOCKET_DIR: /var/run/powerdns-recursor
      ENV_SOCKET_MODE: 660
      ENV_LOCAL_ADDRESS: 192.168.100.20
      ENV_LOCAL_PORT: 53
      ENV_USE_INCOMING_EDNS_SUBNET: "yes"
      ENV_ECS_IPV4_BITS: 32
      ENV_ECS_IPV6_BITS: 128
      ENV_QUIET: "yes"
      ENV_SETGID: pdns
      ENV_SETUID: pdns
      ENV_DNSSEC: "off"
      ENV_WEBSERVER: "yes"
      ENV_WEBSERVER_PASSWORD: CHANGEME_PASSWORD
      ENV_WEBSERVER_ADDRESS: 0.0.0.0
      ENV_WEBSERVER_ALLOW_FROM: 0.0.0.0/0
      ENV_WEBSERVER_PORT: 8002
      ENV_API_KEY: CHANGEME_PASSWORD
      PDNS_AUTH_API_HOST: 127.0.0.1
      PDNS_AUTH_API_DNS_PORT: 5300
      PDNS_AUTH_API_PORT: 8001
      PDNS_AUTH_API_KEY: CHANGEME_PASSWORD
      EXTRA_FORWARD: ""
```

## Development

### TODO

- [ ] Automate builds with github actions
- [ ] Rewrite so that the builds are using Major, Mini, Micro releases tagging.
- [ ] Backup - Run a backup of the DB when detecting a new schema just before running the schema.
- [ ] Migration Upgrade/Downgrade - With backup, be able to essentially roll back to the previous version.

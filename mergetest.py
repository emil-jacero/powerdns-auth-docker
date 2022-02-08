import json


def merge_dicts(base_dict, dict_list):
    for dict in dict_list:
        base_dict.update(dict)
    return base_dict


# Default pdns config as dict
## "gsqlite3-database": "/var/lib/powerdns/auth.db",
## "gsqlite3-pragma-synchronous": 0,
defaults = {
    "setuid": 101,
    "setgid": 101,
    "primary": "yes",
    "secondary": "no",
    "launch": "gsqlite3",
    "gsqlite3-database": "/var/lib/powerdns/auth.db",
    "local-address": "0.0.0.0",
    "local-port": 53
}
extra1 = {
    "launch": "gpgsql",
    "gpgsql-dbname": "pdns",
    "gpgsql-user": "pdns",
    "gpgsql-password": "pdns",
    "gpgsql-host": "db",
    "gpgsql-port": 5432,
    "extra1": "extra1"
}
extra2 = {
    "launch": "gpgsql",
    "gpgsql-dbname": "pdns2",
    "gpgsql-user": "pdns2",
    "gpgsql-password": "pdns",
    "gpgsql-host": "db",
    "gpgsql-port": 5432,
    "extra2": "extra2"
}

merged = merge_dicts(defaults, [extra1, extra2])
print(json.dumps(merged, indent=2))

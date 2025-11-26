LINKS = [
    "https://raw.githubusercontent.com/ALIILAPRO/v2rayNG-Config/main/sub.txt",
    "https://raw.githubusercontent.com/a2470982985/getNode/main/v2ray.txt",
    "https://raw.githubusercontent.com/aiboboxx/v2rayfree/main/v2",
    "https://raw.githubusercontent.com/Flik6/getNode/main/v2ray.txt",
    "https://raw.githubusercontent.com/Leon406/SubCrawler/main/sub/share/vless",
    "https://raw.githubusercontent.com/mahdibland/ShadowsocksAggregator/master/Eternity",
    "https://raw.githubusercontent.com/mfuu/v2ray/master/merge/merge_base64.txt",
    "https://raw.githubusercontent.com/mfuu/v2ray/master/v2ray",
    "https://raw.githubusercontent.com/mlabalabala/v2ray-node/main/nodefree_nodes_mod.txt",
    "https://raw.githubusercontent.com/peasoft/NoMoreWalls/master/list.txt",
    "https://raw.githubusercontent.com/Syavar/V2ray-Configs/main/OK_google.com_base64.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-config/main/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/davudsedft/newpurnet/main/purkow.txt",
    "https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/MhdiTaheri/V2rayCollector_Py/main/sub/Mix/mix.txt",
    "https://raw.githubusercontent.com/MrMohebi/xray-proxy-grabber-telegram/master/collected-proxies/row-url/all.txt",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/splitted/vmess.txt",
    "https://raw.githubusercontent.com/ndsphonemy/proxy-sub/main/default.txt",
    "https://raw.githubusercontent.com/ndsphonemy/proxy-sub/main/speed.txt",
]

DB_PATH = "data/database.db"
URIS_RAW_PATH = "output/uris_raw.txt"
URIS_RAW_REJECTED_PATH = "output/uris_raw_rejected.txt"
URIS_TRANSFORM_PATH = "output/uris_transform.json"

PROXIES = {
    "PROTOCOLS": {
        "vless": {
            "address": {
                "required": True,
                "type": "string",
                "processors": ["to_lower"],
                "validators": ["ipv4", "ipv6", "domain"],
            },
            "port": {
                "required": True,
                "type": "int",
                "validators": ["port"],
            },
            "id": {
                "required": True,
                "type": "string",
            },
            "encryption": {
                "required": False,
                "type": "string",
                "default": "none",
                "allowed": ["none"],
                "source": "params",
                "processors": ["to_lower"],
            },
            "flow": {
                "required": False,
                "type": "string",
                "allowed": {"xtls-rprx-vision", "xtls-rprx-vision-udp443"},
                "source": "params",
                "processors": ["to_lower"],
            },
        },
        "trojan": {
            "address": {
                "required": True,
                "type": "string",
                "processors": ["to_lower"],
                "validators": ["ipv4", "ipv6", "domain"],
            },
            "port": {
                "required": True,
                "type": "int",
                "validators": ["port"],
            },
            "password": {
                "required": True,
                "type": "string",
            },
        },
        "ss": {
            "address": {
                "required": True,
                "type": "string",
                "processors": ["to_lower"],
                "validators": ["ipv4", "ipv6", "domain"],
            },
            "port": {
                "required": True,
                "type": "int",
                "validators": ["port"],
            },
            "method": {
                "required": True,
                "type": "string",
                "allowed": [
                    "2022-blake3-aes-128-gcm",
                    "2022-blake3-aes-256-gcm",
                    "2022-blake3-chacha20-poly1305",
                    "aes-256-gcm",
                    "aes-128-gcm",
                    "chacha20-poly1305",
                    "chacha20-ietf-poly1305",
                    "xchacha20-poly1305",
                    "xchacha20-ietf-poly1305",
                    "none",
                    "plain",
                ],
            },
            "password": {
                "required": True,
                "type": "string",
            },
        },
        "vmess": {
            "address": {
                "required": True,
                "type": "string",
                "processors": ["to_lower"],
                "validators": ["ipv4", "ipv6", "domain"],
            },
            "port": {
                "required": True,
                "type": "int",
                "validators": ["port"],
            },
            "id": {
                "required": True,
                "type": "string",
            },
            "encryption": {
                "required": False,
                "type": "string",
                "default": "auto",
                "allowed": [
                    "aes-128-gcm",
                    "chacha20-poly1305",
                    "auto",
                    "none",
                    "zero",
                ],
                "source": "params",
                "processors": ["to_lower"],
            },
        },
        "hysteria2": {
            "address": {
                "required": True,
                "type": "string",
                "processors": ["to_lower"],
                "validators": ["ipv4", "ipv6", "domain"],
            },
            "port": {
                "required": True,
                "type": "int",
                "validators": ["port"],
            },
            "password": {
                "required": True,
                "type": "string",
            },
            "insecure": {
                "required": True,
                "type": "string",
                "default": "0",
                "allowed": ["0", "1"],
                "source": "params",
            },
            "sni": {
                "required": False,
                "type": "string",
                "source": "params",
                "processors": ["to_lower"],
                "validators": ["host"],
            },
            "pinSHA256": {
                "required": False,
                "type": "string",
                "source": "params",
            },
            "obfs": {
                "required": False,
                "type": "string",
                "allowed": ["salamander"],
                "source": "params",
            },
            "obfs-password": {
                "required": False,
                "type": "string",
                "source": "params",
            },
        },
        "hy2": {
            "uri": {
                "processors": ["to_hysteria2"],
            }
        },
    },
    "TRANSPORTS": {
        "ws": {
            "host": {
                "required": False,
                "type": "string",
                "source": "params",
                "processors": ["to_lower"],
                "validators": ["host"],
            },
            "path": {
                "required": True,
                "type": "string",
                "default": "/",
                "source": "params",
            },
        },
        "httpupgrade": {
            "host": {
                "required": False,
                "type": "string",
                "source": "params",
                "processors": ["to_lower"],
                "validators": ["host"],
            },
            "path": {
                "required": True,
                "type": "string",
                "default": "/",
                "source": "params",
            },
        },
        "xhttp": {
            "host": {
                "required": False,
                "type": "string",
                "source": "params",
                "processors": ["to_lower"],
                "validators": ["host"],
            },
            "path": {
                "required": True,
                "type": "string",
                "default": "/",
                "source": "params",
            },
            "mode": {
                "required": True,
                "type": "string",
                "default": "auto",
                "source": "params",
                "processors": ["to_lower"],
                "allowed": ["auto", "packet-up", "stream-up", "stream-one"],
            },
            "extra": {
                "required": False,
                "type": "dict",
                "source": "params",
            },
        },
        "grpc": {
            "serviceName": {
                "required": False,
                "type": "string",
                "source": "params",
            },
            "mode": {
                "required": True,
                "type": "string",
                "default": "gun",
                "source": "params",
                "processors": ["to_lower"],
                "allowed": ["gun", "multi"],
            },
            "authority": {
                "required": False,
                "type": "string",
                "source": "params",
            },
        },
        "raw": {
            "headerType": {
                "required": False,
                "type": "string",
                "default": "none",
                "source": "params",
                "processors": ["to_lower"],
                "allowed": {"none", "http"},
            },
            "host": {
                "required": False,
                "type": "list",
                "source": "params",
                "processors": ["to_lower", "split_comma_to_list"],
            },
            "path": {
                "required": False,
                "type": "list",
                "default": ["/"],
                "source": "params",
                "processors": ["split_comma_to_list"],
            },
        },
    },
    "SECURITIES": {
        "tls": {
            "sni": {
                "required": False,
                "type": "string",
                "source": "params",
                "processors": ["to_lower"],
                "validators": ["host"],
            },
            "fp": {
                "required": False,
                "type": "string",
                "source": "params",
                "processors": ["to_lower"],
                "allowed": {
                    "chrome",
                    "firefox",
                    "safari",
                    "ios",
                    "android",
                    "edge",
                    "360",
                    "qq",
                    "random",
                    "randomized",
                },
            },
            "alpn": {
                "required": False,
                "type": "list",
                "default": ["h2", "http/1.1"],
                "source": "params",
                "processors": ["split_comma_to_list"],
                "allowed": {"h2", "http/1.1", "http/1.0", "fromMitM"},
            },
        },
        "reality": {
            "sni": {
                "required": False,
                "type": "string",
                "source": "params",
                "processors": ["to_lower"],
                "validators": ["host"],
            },
            "fp": {
                "required": False,
                "type": "string",
                "source": "params",
                "processors": ["to_lower"],
                "allowed": {
                    "chrome",
                    "firefox",
                    "safari",
                    "ios",
                    "android",
                    "edge",
                    "360",
                    "qq",
                    "random",
                    "randomized",
                },
            },
            "pbk": {
                "required": False,
                "type": "string",
                "source": "params",
            },
            "sid": {
                "required": False,
                "type": "string",
                "source": "params",
            },
            "spx": {
                "required": False,
                "type": "string",
                "source": "params",
            },
        },
        "none": {},
    },
}

TABLE_SCHEMAS = {
    "uris_raw": {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "uri": "TEXT NOT NULL UNIQUE",
        "hash": "TEXT",
        "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
        "updated_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
    },
    "uris_rejected": {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "line": "TEXT NOT NULL",
        "source_url": "TEXT",
        "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
    },
}

configs_map = {
    "LINKS": LINKS,
    "DB_PATH": DB_PATH,
    "URIS_RAW_PATH": URIS_RAW_PATH,
    "URIS_RAW_REJECTED_PATH": URIS_RAW_REJECTED_PATH,
    "URIS_TRANSFORM_PATH": URIS_TRANSFORM_PATH,
    "PROXIES": PROXIES,
    "TABLE_SCHEMAS": TABLE_SCHEMAS,
}

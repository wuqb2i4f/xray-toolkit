# List of URLs to process
LINKS = [
    # "https://raw.githubusercontent.com/ALIILAPRO/v2rayNG-Config/main/sub.txt",
    # "https://raw.githubusercontent.com/a2470982985/getNode/main/v2ray.txt",
    # "https://raw.githubusercontent.com/aiboboxx/v2rayfree/main/v2",
    # "https://raw.githubusercontent.com/Flik6/getNode/main/v2ray.txt",
    # "https://raw.githubusercontent.com/Leon406/SubCrawler/main/sub/share/vless",
    # "https://raw.githubusercontent.com/mahdibland/ShadowsocksAggregator/master/Eternity",
    "https://raw.githubusercontent.com/mfuu/v2ray/master/merge/merge_base64.txt",
    # "https://raw.githubusercontent.com/mfuu/v2ray/master/v2ray",
    # "https://raw.githubusercontent.com/mlabalabala/v2ray-node/main/nodefree_nodes_mod.txt",
    # "https://raw.githubusercontent.com/peasoft/NoMoreWalls/master/list.txt",
    # "https://raw.githubusercontent.com/Syavar/V2ray-Configs/main/OK_google.com_base64.txt",
    # "https://raw.githubusercontent.com/barry-far/V2ray-config/main/All_Configs_Sub.txt",
    # "https://raw.githubusercontent.com/davudsedft/newpurnet/main/purkow.txt",
    "https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/All_Configs_Sub.txt",
    # "https://raw.githubusercontent.com/MhdiTaheri/V2rayCollector_Py/main/sub/Mix/mix.txt",
    # "https://raw.githubusercontent.com/MrMohebi/xray-proxy-grabber-telegram/master/collected-proxies/row-url/all.txt",
    # "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/splitted/vmess.txt",
    # "https://raw.githubusercontent.com/ndsphonemy/proxy-sub/main/default.txt",
    # "https://raw.githubusercontent.com/ndsphonemy/proxy-sub/main/speed.txt",
]

# Database settings
DB_PATH = "data/database.db"

# Extract output path
REJECTED_URIS_PATH = "output/raw_uris_rejected.txt"

# Unified proxies config
PROXIES = {
    "PROTOCOLS": {
        "vless": {"uri": {"output": "output/raw_uris_vless.txt"}},
        "trojan": {"uri": {"output": "output/raw_uris_trojan.txt"}},
        "ss": {"uri": {"output": "output/raw_uris_ss.txt"}},
        "vmess": {"uri": {"output": "output/raw_uris_vmess.txt"}},
        "hysteria2": {"uri": {"output": "output/raw_uris_hysteria2.txt"}},
        "hy2": {
            "uri": {
                "output": "output/raw_uris_hysteria2.txt",
                "normalize": "map_to_hysteria2",
            },
        },
    },
}

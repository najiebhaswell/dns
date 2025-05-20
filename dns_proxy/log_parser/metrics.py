from collections import Counter, defaultdict

def get_unbound_data():
    return defaultdict(lambda: {
        "qps": 0.0, "query_types": Counter(), "response_codes": Counter(), "query_count": 0
    })

def get_dns_proxy_data():
    return defaultdict(lambda: {
        "qps": 0.0, "query_types": Counter(), "response_codes": Counter(),
        "blocked_domains": [], "query_count": 0
    })

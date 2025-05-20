import time
import logging
from datetime import datetime
from .config import *
from .regex_patterns import *
from .metrics import get_unbound_data, get_dns_proxy_data

unbound_data = get_unbound_data()
dns_proxy_data = get_dns_proxy_data()
unbound_last_position = 0
dns_proxy_last_position = 0

def parse_timestamp(timestamp_str, source="unbound"):
    try:
        if source == "unbound":
            return int(timestamp_str)
        return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S,%f").timestamp()
    except ValueError as e:
        logging.error(f"Error parsing timestamp ({source}): {e}")
        return None

def parse_log():
    global unbound_last_position, dns_proxy_last_position
    current_time = time.time()
    # Temp struktur per window
    uw_q = defaultdict(list)
    dp_q = defaultdict(list)
    uw_types = defaultdict(Counter)
    dp_types = defaultdict(Counter)
    uw_resp = defaultdict(Counter)
    dp_resp = defaultdict(Counter)
    dp_blocked = defaultdict(list)

    # Parse Unbound log
    try:
        with open(UNBOUND_LOG_FILE, 'r') as f:
            f.seek(unbound_last_position)
            lines = [next(f) for _ in range(MAX_LINES_PER_READ) if f.tell() != 0]
            unbound_last_position = f.tell()
        for line in lines:
            match = UNBOUND_PATTERN.search(line)
            if match:
                timestamp_str, domain, query_type, class_, response_code = match.groups()
                timestamp = parse_timestamp(timestamp_str, "unbound")
                if timestamp and timestamp >= current_time - MAX_STORAGE_SECONDS:
                    window = int(timestamp - (timestamp % WINDOW_SECONDS))
                    uw_q[window].append(timestamp)
                    uw_types[window][query_type] += 1
                    if response_code:
                        uw_resp[window][response_code] += 1
    except Exception as e:
        logging.error(f"Error reading Unbound log file: {e}")

    # Parse DNS Proxy log
    try:
        with open(DNS_PROXY_LOG_FILE, 'r') as f:
            f.seek(dns_proxy_last_position)
            lines = [next(f) for _ in range(MAX_LINES_PER_READ) if f.tell() != 0]
            dns_proxy_last_position = f.tell()
        for line in lines:
            match_fwd = DNS_PROXY_FORWARD_PATTERN.search(line)
            match_safe = DNS_PROXY_SAFESEARCH_PATTERN.search(line)
            match_block = DNS_PROXY_BLOCK_PATTERN.search(line)
            if match_fwd:
                timestamp_str, domain = match_fwd.groups()
                timestamp = parse_timestamp(timestamp_str, "dns_proxy")
                if timestamp and timestamp >= current_time - MAX_STORAGE_SECONDS:
                    window = int(timestamp - (timestamp % WINDOW_SECONDS))
                    dp_q[window].append(timestamp)
                    dp_types[window]['A'] += 1
                    dp_resp[window]['NOERROR'] += 1
            if match_safe:
                timestamp_str, domain = match_safe.groups()
                timestamp = parse_timestamp(timestamp_str, "dns_proxy")
                if timestamp and timestamp >= current_time - MAX_STORAGE_SECONDS:
                    window = int(timestamp - (timestamp % WINDOW_SECONDS))
                    dp_q[window].append(timestamp)
                    dp_types[window]['CNAME'] += 1
                    dp_resp[window]['NOERROR'] += 1
            if match_block:
                timestamp_str, domain = match_block.groups()
                timestamp = parse_timestamp(timestamp_str, "dns_proxy")
                if timestamp and timestamp >= current_time - MAX_STORAGE_SECONDS:
                    window = int(timestamp - (timestamp % WINDOW_SECONDS))
                    dp_q[window].append(timestamp)
                    dp_types[window]['A'] += 1
                    dp_resp[window]['NXDOMAIN'] += 1
                    dp_blocked[window].append(domain)
    except Exception as e:
        logging.error(f"Error reading DNS Proxy log file: {e}")

    # Update data
    for window in uw_q:
        qps = len(uw_q[window]) / WINDOW_SECONDS
        unbound_data[window]["qps"] = qps
        unbound_data[window]["query_types"] += uw_types[window]
        unbound_data[window]["response_codes"] += uw_resp[window]
        unbound_data[window]["query_count"] += len(uw_q[window])
    for window in dp_q:
        qps = len(dp_q[window]) / WINDOW_SECONDS
        dns_proxy_data[window]["qps"] = qps
        dns_proxy_data[window]["query_types"] += dp_types[window]
        dns_proxy_data[window]["response_codes"] += dp_resp[window]
        dns_proxy_data[window]["blocked_domains"].extend(dp_blocked[window])
        dns_proxy_data[window]["query_count"] += len(dp_q[window])
    # Cleanup old
    for data in [unbound_data, dns_proxy_data]:
        for ts in list(data.keys()):
            if current_time - ts > MAX_STORAGE_SECONDS:
                del data[ts]

def get_data(range_seconds=50):
    parse_log()
    current_time = time.time()
    start_time = current_time - range_seconds
    # Unbound
    unbound_qps, unbound_types, unbound_resp, unbound_timestamps = [], Counter(), Counter(), []
    for t in sorted(t for t in unbound_data if t >= start_time):
        d = unbound_data[t]
        unbound_qps.append(d["qps"])
        unbound_types.update(d["query_types"])
        unbound_resp.update(d["response_codes"])
        unbound_timestamps.append(t)
    # DNS Proxy
    dns_qps, dns_types, dns_resp, dns_blocked, dns_timestamps = [], Counter(), Counter(), [], []
    for t in sorted(t for t in dns_proxy_data if t >= start_time):
        d = dns_proxy_data[t]
        dns_qps.append(d["qps"])
        dns_types.update(d["query_types"])
        dns_resp.update(d["response_codes"])
        dns_blocked.extend(d["blocked_domains"])
        dns_timestamps.append(t)
    dns_blocked = dns_blocked[-50:]
    all_timestamps = sorted(set(unbound_timestamps + dns_timestamps))
    return {
        "unbound": {
            "qps": unbound_qps,
            "queryTypes": [unbound_types.get(t, 0) for t in ['A', 'CNAME', 'MX', 'AAAA', 'TXT', 'PTR']],
            "responseCodes": [unbound_resp.get(c, 0) for c in ['NOERROR', 'NXDOMAIN', 'SERVFAIL']],
            "timestamps": unbound_timestamps,
        },
        "dns_proxy": {
            "qps": dns_qps,
            "queryTypes": [dns_types.get(t, 0) for t in ['A', 'CNAME', 'MX', 'AAAA', 'TXT', 'PTR']],
            "responseCodes": [dns_resp.get(c, 0) for c in ['NOERROR', 'NXDOMAIN', 'SERVFAIL']],
            "blockedDomains": dns_blocked,
            "timestamps": dns_timestamps,
        },
        "all_timestamps": all_timestamps
    }
import logging
from .config import LOG_FILE, UNBOUND_LOG_FILE, DNS_PROXY_LOG_FILE
from .api_server import run_server

def reset_log_position(path):
    try:
        with open(path, 'r') as f:
            f.seek(0, 2)
            return f.tell()
    except Exception:
        return 0

def main():
    logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                        format="%(asctime)s - %(levelname)s - %(message)s")
    from .parser import unbound_last_position, dns_proxy_last_position
    unbound_last_position = reset_log_position(UNBOUND_LOG_FILE)
    dns_proxy_last_position = reset_log_position(DNS_PROXY_LOG_FILE)
    run_server()

if __name__ == "__main__":
    main()

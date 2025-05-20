import logging
import threading
from .config import LOG_FILE
from .acl import start_acl_watcher
from .handler import DNSHandler

def start_ipv4_server():
    from socketserver import ThreadingUDPServer
    server = ThreadingUDPServer(("0.0.0.0", 53), DNSHandler)
    logging.info("IPv4 DNS proxy server started on 0.0.0.0:53")
    server.serve_forever()

def start_ipv6_server():
    from socketserver import ThreadingUDPServer
    import socket
    server = ThreadingUDPServer(("::", 53), DNSHandler, False)
    server.socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    server.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)
    server.socket.bind(("::", 53))
    logging.info("IPv6 DNS proxy server started on ::::53")
    server.serve_forever()

def main():
    logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                        format="%(asctime)s - %(levelname)s - %(message)s")
    start_acl_watcher()
    ipv4_thread = threading.Thread(target=start_ipv4_server)
    ipv6_thread = threading.Thread(target=start_ipv6_server)
    ipv4_thread.start()
    ipv6_thread.start()
    try:
        ipv4_thread.join()
        ipv6_thread.join()
    except KeyboardInterrupt:
        logging.info("DNS proxy server stopped")

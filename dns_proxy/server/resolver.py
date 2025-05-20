import sqlite3
import logging
import socket
from dnslib import DNSRecord, QTYPE, RCODE, RR, CNAME, A, AAAA, EDNS0
from .config import DATABASE_FILE, BLOCK_DOMAIN, BLOCK_IP, BLOCK_IP6

def query_domain(qname):
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute("SELECT blocked, type, cname FROM domains WHERE domain = ?", (qname,))
    row = c.fetchone()
    logging.info(f"Database query result: {row}")
    conn.close()
    return row

def resolve_to_a_record(qname, upstream_ip, upstream_port):
    request = DNSRecord.question(qname, qtype="A")
    upstream_socket = socket.socket(
        socket.AF_INET if ':' not in upstream_ip else socket.AF_INET6,
        socket.SOCK_DGRAM
    )
    upstream_socket.settimeout(5)
    try:
        upstream_socket.sendto(request.pack(), (upstream_ip, upstream_port))
        response_data, _ = upstream_socket.recvfrom(1024)
        response = DNSRecord.parse(response_data)
        max_redirects = 10
        current_name = qname
        for _ in range(max_redirects):
            for rr in response.rr:
                if rr.rtype == QTYPE.A:
                    return str(rr.rdata)
                elif rr.rtype == QTYPE.CNAME:
                    current_name = str(rr.rdata)
                    request = DNSRecord.question(current_name, qtype="A")
                    upstream_socket.sendto(request.pack(), (upstream_ip, upstream_port))
                    response_data, _ = upstream_socket.recvfrom(1024)
                    response = DNSRecord.parse(response_data)
                    break
            else:
                break
        return None
    except Exception as e:
        logging.error(f"Error resolving {qname}: {str(e)}")
        return None
    finally:
        upstream_socket.close()

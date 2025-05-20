import logging
import socket
import ipaddress
from dnslib import DNSRecord, QTYPE, RCODE, RR, CNAME, A, AAAA, EDNS0, DNSError
from socketserver import ThreadingUDPServer, BaseRequestHandler
from .config import *
from .acl import ALLOWED_NETWORKS
from .resolver import query_domain, resolve_to_a_record

class DNSHandler(BaseRequestHandler):
    def is_allowed(self, client_ip):
        try:
            client_ip = ipaddress.ip_address(client_ip)
            return any(client_ip in network for network in ALLOWED_NETWORKS)
        except ValueError:
            return False

    def handle(self):
        try:
            data, sock = self.request
            client_ip = self.client_address[0]
            if not self.is_allowed(client_ip):
                try:
                    header = DNSRecord.parse(data).header
                    reply = DNSRecord()
                    reply.header.id = header.id
                except DNSError:
                    reply = DNSRecord()
                reply.header.qr = 1
                reply.header.rcode = RCODE.REFUSED
                sock.sendto(reply.pack(), self.client_address)
                return

            # Defensive: minimal DNS packet length is 12 bytes
            if len(data) < 12:
                logging.warning(f"Received too short DNS packet from {client_ip}: {len(data)} bytes")
                return

            # Defensive: parse DNS with try/except for malformed packets
            try:
                request = DNSRecord.parse(data)
            except DNSError as e:
                logging.warning(f"Malformed DNS packet from {client_ip}: {e}")
                return

            qname = str(request.q.qname).rstrip('.')
            upstream_ip = UPSTREAM_DNS if ':' not in client_ip else UPSTREAM_DNS6
            upstream_port = UPSTREAM_PORT

            row = query_domain(qname)
            if row:
                blocked, dtype, cname = row
                if dtype == "safesearch" and cname:
                    ip_address = resolve_to_a_record(cname, upstream_ip, upstream_port)
                    reply = request.reply()
                    reply.add_answer(RR(
                        rname=qname,
                        rtype=QTYPE.CNAME,
                        ttl=86400,
                        rdata=CNAME(cname)
                    ))
                    if ip_address:
                        reply.add_answer(RR(
                            rname=cname,
                            rtype=QTYPE.A,
                            ttl=3600,
                            rdata=A(ip_address)
                        ))
                    sock.sendto(reply.pack(), self.client_address)
                    return
                elif blocked:
                    reply = request.reply()
                    reply.add_answer(RR(
                        rname=qname,
                        rtype=QTYPE.CNAME,
                        ttl=86400,
                        rdata=CNAME(BLOCK_DOMAIN)
                    ))
                    if request.q.qtype == QTYPE.A or request.q.qtype == QTYPE.ANY:
                        reply.add_answer(RR(
                            rname=BLOCK_DOMAIN,
                            rtype=QTYPE.A,
                            ttl=3600,
                            rdata=A(BLOCK_IP)
                        ))
                    if request.q.qtype == QTYPE.AAAA or request.q.qtype == QTYPE.ANY:
                        reply.add_answer(RR(
                            rname=BLOCK_DOMAIN,
                            rtype=QTYPE.AAAA,
                            ttl=3600,
                            rdata=AAAA(BLOCK_IP6)
                        ))
                    sock.sendto(reply.pack(), self.client_address)
                    return

            # Forward to upstream
            upstream = (upstream_ip, upstream_port)
            upstream_socket = socket.socket(
                socket.AF_INET if ':' not in upstream_ip else socket.AF_INET6,
                socket.SOCK_DGRAM
            )
            upstream_socket.settimeout(5)
            try:
                upstream_socket.sendto(data, upstream)
                response, _ = upstream_socket.recvfrom(1024)
                sock.sendto(response, self.client_address)
            finally:
                upstream_socket.close()
        except Exception as e:
            logging.error(f"Error processing query: {str(e)}", exc_info=True)

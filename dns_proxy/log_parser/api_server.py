from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import logging
from .parser import get_data
from .config import SERVER_PORT

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        logging.info("Received API request")
        range_seconds = 50
        try:
            range_seconds = int(self.headers.get('X-Time-Range', 50))
        except Exception:
            pass
        data = get_data(range_seconds)
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
        logging.info("API request completed")

def run_server():
    server_address = ('', SERVER_PORT)
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    logging.info(f"Server running on port {SERVER_PORT}...")
    httpd.serve_forever()

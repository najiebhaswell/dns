import json
import ipaddress
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
import time
from .config import ACL_FILE

ALLOWED_NETWORKS = []

def load_acl():
    global ALLOWED_NETWORKS
    try:
        with open(ACL_FILE, 'r') as f:
            acl_data = json.load(f)
            ALLOWED_NETWORKS = [ipaddress.ip_network(ip, strict=False) for ip in acl_data["allowed_ips"]]
        logging.info(f"Loaded ACL: {ALLOWED_NETWORKS}")
    except Exception as e:
        logging.error(f"Error loading ACL file: {e}")
        ALLOWED_NETWORKS = []

class ACLFileHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory and event.src_path == ACL_FILE:
            logging.info(f"ACL file modified: {event.src_path}")
            load_acl()

def start_acl_watcher():
    load_acl()
    event_handler = ACLFileHandler()
    observer = Observer()
    observer.schedule(event_handler, path=ACL_FILE, recursive=False)
    observer.start()
    logging.info("Started ACL file watcher")
    def loop():
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
    thread = threading.Thread(target=loop, daemon=True)
    thread.start()
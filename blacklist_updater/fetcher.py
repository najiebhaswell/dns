import os
import pickle
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from .config import SOURCE_URL, TEMP_FILE, VALIDATED_FILE, LAST_MODIFIED_FILE, FILE_HASH_FILE, DOWNLOAD_TIMEOUT
from .validator import compute_file_hash

def fetch_domains():
    headers = {}
    if os.path.exists(LAST_MODIFIED_FILE):
        with open(LAST_MODIFIED_FILE, "rb") as f:
            last_modified = pickle.load(f)
        headers["If-Modified-Since"] = last_modified
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retries))
    try:
        logging.info(f"Downloading blacklist from {SOURCE_URL}")
        response = session.get(SOURCE_URL, headers=headers, stream=True, timeout=DOWNLOAD_TIMEOUT)
        if response.status_code != 304:
            response.raise_for_status()
            with open(TEMP_FILE, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            logging.info(f"Downloaded blacklist to {TEMP_FILE}")
            if "Last-Modified" in response.headers:
                with open(LAST_MODIFIED_FILE, "wb") as f:
                    pickle.dump(response.headers["Last-Modified"], f)
        else:
            logging.info("Blacklist not modified. Using cached file.")
        current_hash = compute_file_hash(TEMP_FILE)
        previous_hash = None
        if os.path.exists(FILE_HASH_FILE):
            with open(FILE_HASH_FILE, "rb") as f:
                previous_hash = pickle.load(f)
        if previous_hash == current_hash and os.path.exists(VALIDATED_FILE):
            logging.info("File content unchanged. Using cached domains.")
            with open(VALIDATED_FILE, "r") as f:
                domains = {line.strip().lower() for line in f if line.strip()}
            return domains
        return None  # File was changed or no cache, so validation needed
    except requests.Timeout:
        logging.error("Download timed out. Using cached file if available.")
        if os.path.exists(VALIDATED_FILE):
            with open(VALIDATED_FILE, "r") as f:
                domains = {line.strip().lower() for line in f if line.strip()}
            logging.info(f"Using cached file with {len(domains)} domains.")
            return domains
        else:
            logging.error("No cached file available. Exiting.")
            return set()
    except Exception as e:
        logging.error(f"Failed to fetch domains: {str(e)}")
        if os.path.exists(VALIDATED_FILE):
            with open(VALIDATED_FILE, "r") as f:
                domains = {line.strip().lower() for line in f if line.strip()}
            logging.info(f"Using cached file with {len(domains)} domains.")
            return domains
        return set()
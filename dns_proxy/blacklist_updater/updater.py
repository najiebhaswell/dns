import time
import logging
from .config import LOG_FILE
from .database import initialize_database, sync_domains, update_safe_search_domains
from .fetcher import fetch_domains
from .validator import validate_and_save_domains

def main():
    logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                        format="%(asctime)s - %(levelname)s - %(message)s")
    start_time = time.time()
    initialize_database()
    # Fetch and validate domains
    domains = fetch_domains()
    if domains is None:
        domains = validate_and_save_domains()
    if not domains:
        logging.error("No domains fetched. Exiting.")
        return
    new_domains, domains_to_delete = sync_domains(domains)
    update_safe_search_domains()
    elapsed_time = time.time() - start_time
    logging.info(f"Database synchronization completed in {elapsed_time:.2f} seconds.")

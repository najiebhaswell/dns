import re
import hashlib
import logging
import os
import pickle
from multiprocessing import Pool, cpu_count
from .config import TEMP_FILE, VALIDATED_FILE, FILE_HASH_FILE

def compute_file_hash(file_path):
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def validate_domain(domain):
    domain = domain.strip().lower()
    if domain and re.match(r'^[a-z0-9-]+\.[a-z0-9-.]+$', domain):
        return domain
    return None

def validate_domains_chunk(chunk):
    return [validate_domain(domain) for domain in chunk]

def validate_and_save_domains():
    with open(TEMP_FILE, "r") as f:
        all_domains = list(f)
    domains = set()
    validated_domains = []
    invalid_count = 0
    num_processes = cpu_count()
    chunk_size = len(all_domains) // num_processes + 1
    chunks = [all_domains[i:i + chunk_size] for i in range(0, len(all_domains), chunk_size)]
    with Pool(processes=num_processes) as pool:
        results = pool.map(validate_domains_chunk, chunks)
    for chunk in results:
        for domain in chunk:
            if domain:
                domains.add(domain)
                validated_domains.append(domain)
            else:
                invalid_count += 1
    with open(VALIDATED_FILE, "w") as f:
        f.write("\n".join(validated_domains) + "\n")
    with open(FILE_HASH_FILE, "wb") as f:
        pickle.dump(compute_file_hash(TEMP_FILE), f)
    logging.info(f"Validated {len(domains)} domains, {invalid_count} invalid domains skipped")
    return domains
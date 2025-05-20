DATABASE_FILE = "/var/lib/unbound/blacklist.db"
SOURCE_URL = "https://trustpositif.komdigi.go.id/assets/db/domains_isp"
TEMP_FILE = "/tmp/blacklist_cached.txt"
VALIDATED_FILE = "/tmp/blacklist_validated.txt"
LAST_MODIFIED_FILE = "/tmp/blacklist_last_modified.pkl"
FILE_HASH_FILE = "/tmp/blacklist_hash.pkl"
LOG_FILE = "/var/log/rpz_update.log"
DOWNLOAD_TIMEOUT = 30

SAFE_SEARCH_DOMAINS = {
    "www.google.com": {"cname": "forcesafesearch.google.com", "type": "safesearch"},
    "www.bing.com": {"cname": "strict.bing.com", "type": "safesearch"}
}
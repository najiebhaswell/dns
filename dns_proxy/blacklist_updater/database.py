import sqlite3
import logging
from .config import DATABASE_FILE, SAFE_SEARCH_DOMAINS

def initialize_database():
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS domains
                 (domain TEXT PRIMARY KEY, blocked INTEGER DEFAULT 1)''')
    c.execute("PRAGMA table_info(domains)")
    columns = [col[1] for col in c.fetchall()]
    if "type" not in columns:
        c.execute("ALTER TABLE domains ADD COLUMN type TEXT")
        c.execute("UPDATE domains SET type = 'block' WHERE type IS NULL")
        logging.info("Added 'type' column to domains table.")
    if "cname" not in columns:
        c.execute("ALTER TABLE domains ADD COLUMN cname TEXT")
        logging.info("Added 'cname' column to domains table.")
    c.execute("CREATE INDEX IF NOT EXISTS idx_domains_domain ON domains(domain)")
    logging.info("Index on 'domain' column created or already exists.")
    conn.commit()
    conn.close()
    logging.info("Database initialized or already exists.")

def get_existing_domains():
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute("SELECT domain, type FROM domains")
    existing_domains = {row[0]: row[1] for row in c.fetchall()}
    conn.close()
    return existing_domains

def sync_domains(source_domains):
    existing_domains = get_existing_domains()
    new_domains = source_domains - {domain for domain, dtype in existing_domains.items() if dtype == "block"}
    domains_to_delete = {domain for domain, dtype in existing_domains.items() if dtype == "block"} - source_domains
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    try:
        conn.execute("BEGIN TRANSACTION")
        for domain in new_domains:
            cname = SAFE_SEARCH_DOMAINS.get(domain, {}).get("cname")
            try:
                c.execute("INSERT INTO domains (domain, blocked, type, cname) VALUES (?, ?, ?, ?)",
                          (domain, 1, "block", cname))
            except sqlite3.IntegrityError:
                continue
        for domain in domains_to_delete:
            c.execute("DELETE FROM domains WHERE domain = ? AND type = 'block'", (domain,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        logging.error(f"Error in database synchronization: {str(e)}")
    finally:
        conn.close()
    return new_domains, domains_to_delete

def update_safe_search_domains():
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    try:
        conn.execute("BEGIN TRANSACTION")
        for domain, info in SAFE_SEARCH_DOMAINS.items():
            c.execute("INSERT OR REPLACE INTO domains (domain, blocked, type, cname) VALUES (?, 0, ?, ?)",
                      (domain, info["type"], info["cname"]))
        conn.commit()
    except Exception as e:
        conn.rollback()
        logging.error(f"Error updating Safe Search domains: {str(e)}")
    finally:
        conn.close()
